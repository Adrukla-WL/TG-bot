"""Entry point for the Viva WaterLand Assistant Telegram bot."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

from openai import OpenAI
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (Application, ApplicationBuilder, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from rag.rag_retriever import RAGRetriever
from utils import markers as marker_parser
from utils import state_manager

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

SECURITY_LOG = LOGS_DIR / "security.log"
INTERACTION_LOG = LOGS_DIR / "interactions.log"
ANALYTICS_LOG = LOGS_DIR / "analytics.log"

SYSTEM_PROMPT_PATH = BASE_DIR / "prompts" / "agent_network_prompt.txt"
DEFAULT_SYSTEM_PROMPT = "Вы — Viva WaterLand Assistant. Используйте только проверенные данные."


class WaterLandBot:
    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required")

        self.system_prompt = self._load_system_prompt()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)

        self.rag = RAGRetriever(
            index_path=str(BASE_DIR / "rag" / "waterland_index_v1.faiss"),
            meta_path=str(BASE_DIR / "rag" / "waterland_meta_v1.parquet"),
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )

        self.application: Application = ApplicationBuilder().token(self.token).build()
        self._configure_logging()
        self._register_handlers()

    def _configure_logging(self) -> None:
        logging.basicConfig(level=logging.INFO)

        self.security_logger = logging.getLogger("waterland.security")
        self.security_logger.setLevel(logging.INFO)
        security_handler = logging.FileHandler(SECURITY_LOG, encoding="utf-8")
        security_handler.setFormatter(logging.Formatter("%(message)s"))
        self.security_logger.addHandler(security_handler)
        self.security_logger.propagate = False

        self.interactions_logger = logging.getLogger("waterland.interactions")
        self.interactions_logger.setLevel(logging.INFO)
        interactions_handler = logging.FileHandler(INTERACTION_LOG, encoding="utf-8")
        interactions_handler.setFormatter(logging.Formatter("%(message)s"))
        self.interactions_logger.addHandler(interactions_handler)

        self.analytics_logger = logging.getLogger("waterland.analytics")
        self.analytics_logger.setLevel(logging.INFO)
        analytics_handler = logging.FileHandler(ANALYTICS_LOG, encoding="utf-8")
        analytics_handler.setFormatter(logging.Formatter("%(message)s"))
        self.analytics_logger.addHandler(analytics_handler)

    def _register_handlers(self) -> None:
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def _load_system_prompt(self) -> str:
        try:
            return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logging.warning("System prompt file not found at %s; using default prompt.", SYSTEM_PROMPT_PATH)
            return DEFAULT_SYSTEM_PROMPT

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Здравствуйте! Я Viva WaterLand Assistant. Задайте свой вопрос, и я постараюсь помочь на основе официальной базы WaterLand."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user is None or update.message is None:
            return

        user_id = update.effective_user.id
        user_message = update.message.text or ""

        session = state_manager.load_session(user_id)
        state_manager.update_context_history(user_id, "user", user_message)

        self._log_interaction(user_id, "user", user_message)

        if self._is_potential_prompt_leak(user_message):
            warning = "Извините, я не могу обсуждать внутренние инструкции."
            await self._send_reply(update, warning)
            self._log_security_event(
                event_type="prompt_leak_attempt",
                user_id=user_id,
                payload={"message": user_message},
            )
            state_manager.update_context_history(user_id, "assistant", warning)
            return

        rag_chunks = self.rag.search(user_message)
        if not rag_chunks:
            fallback = "Информация не найдена в официальной базе WaterLand."
            await self._send_reply(update, fallback)
            self._log_interaction(user_id, "assistant", fallback)
            state_manager.update_context_history(user_id, "assistant", fallback)
            return

        context_block = self._assemble_context(rag_chunks)

        llm_response = await self._call_llm(context_block, user_message)
        if llm_response is None:
            fallback = "Не удалось получить ответ от модели. Пожалуйста, попробуйте позже."
            await self._send_reply(update, fallback)
            state_manager.update_context_history(user_id, "assistant", fallback)
            return

        parsed = marker_parser.extract_markers(llm_response)
        markers = parsed.get("markers", {})

        self._log_interaction(user_id, "assistant", parsed["clean_text"], markers)
        self._log_analytics(user_id, markers)
        self._handle_security_markers(user_id, markers, user_message)

        state = session
        state.update({"markers": markers})
        state_manager.save_session(user_id, state)
        state_manager.update_context_history(user_id, "assistant", parsed["clean_text"], markers=markers)

        await self._send_reply(update, parsed["clean_text"])

    async def _call_llm(self, context_block: str, user_message: str) -> str | None:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Контекст:\n{context_block}"},
            {"role": "user", "content": user_message},
        ]

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logging.exception("Failed to call LLM: %s", exc)
            return None

    def _assemble_context(self, chunks: List[Any]) -> str:
        if not chunks:
            return "Информация не найдена в официальной базе WaterLand."

        formatted = []
        for idx, chunk in enumerate(chunks, start=1):
            snippet = chunk.text or chunk.metadata.get("text", "")
            source = chunk.metadata.get("source", "неизвестный источник")
            formatted.append(f"[{idx}] Источник: {source}\n{snippet}")
        return "\n\n".join(formatted)

    def _is_potential_prompt_leak(self, message: str) -> bool:
        lowered = message.lower()
        triggers = ["раскрой свой промт", "system prompt", "инструкц", "промт"]
        return any(trigger in lowered for trigger in triggers)

    async def _send_reply(self, update: Update, text: str) -> None:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    def _log_interaction(self, user_id: int, role: str, message: str, markers: Dict[str, Any] | None = None) -> None:
        payload = {
            "user_id": user_id,
            "role": role,
            "message": message,
            "markers": markers or {},
        }
        self.interactions_logger.info(json.dumps(payload, ensure_ascii=False))

    def _log_analytics(self, user_id: int, markers: Dict[str, Any]) -> None:
        payload = {
            "user_id": user_id,
            "intent": markers.get("intent"),
            "branch": markers.get("branch"),
        }
        self.analytics_logger.info(json.dumps(payload, ensure_ascii=False))

    def _handle_security_markers(self, user_id: int, markers: Dict[str, Any], message: str) -> None:
        if "security" in markers:
            self._log_security_event(
                event_type="agent_security_marker",
                user_id=user_id,
                payload={
                    "marker": markers["security"],
                    "message": message,
                },
            )

    def _log_security_event(self, event_type: str, user_id: int, *, payload: Dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "user_id": user_id,
            **payload,
        }
        self.security_logger.info(json.dumps(record, ensure_ascii=False))

    def run(self) -> None:
        self.application.run_polling()


def main() -> None:
    bot = WaterLandBot()
    bot.run()


if __name__ == "__main__":
    main()
