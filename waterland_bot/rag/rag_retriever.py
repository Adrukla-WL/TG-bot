"""RAG Retriever implementation using FAISS and sentence transformers."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

LOGGER = logging.getLogger(__name__)


@dataclass
class RAGChunk:
    text: str
    metadata: dict


class RAGRetriever:
    """Retrieve relevant knowledge base chunks for user queries."""

    def __init__(self, index_path: str, meta_path: str, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") -> None:
        self.index_path = index_path
        self.meta_path = meta_path
        self.model_name = model_name

        self.model = SentenceTransformer(model_name)
        self.index = self._load_index(index_path)
        self.metadata = self._load_metadata(meta_path)

    def _load_index(self, path: str) -> faiss.Index:
        if not os.path.exists(path):
            LOGGER.warning("FAISS index not found at %s. Searches will return empty results.", path)
            return faiss.IndexFlatIP(self.model.get_sentence_embedding_dimension())
        return faiss.read_index(path)

    def _load_metadata(self, path: str) -> pd.DataFrame:
        if not os.path.exists(path):
            LOGGER.warning("Metadata parquet not found at %s. Searches will return empty metadata.", path)
            return pd.DataFrame()
        return pd.read_parquet(path)

    def embed(self, text: str) -> np.ndarray:
        """Generate a normalized embedding for ``text``."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    def search(self, query: str, top_k: int = 5) -> List[RAGChunk]:
        """Search the FAISS index and return the top matching chunks."""
        if self.index.ntotal == 0:
            LOGGER.warning("FAISS index is empty. Returning no results.")
            return []

        query_embedding = self.embed(query)
        scores, indices = self.index.search(np.array([query_embedding]), top_k)

        results: List[RAGChunk] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            metadata = self.metadata.iloc[int(idx)].to_dict() if not self.metadata.empty else {}
            chunk_text = metadata.get("text", "")
            results.append(RAGChunk(text=chunk_text, metadata={"score": float(score), **metadata}))
        return results
