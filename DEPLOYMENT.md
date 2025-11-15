# Развёртывание проекта в репозитории GitHub

Этот репозиторий уже содержит полную структуру проекта «Viva WaterLand Assistant». Чтобы загрузить файлы в удалённый репозиторий `Adrukla-WL/TG-bot`, выполните действия из командной строки с доступом к GitHub:

1. Клонируйте удалённый репозиторий (если ещё не сделано):
   ```bash
   git clone git@github.com:Adrukla-WL/TG-bot.git
   cd TG-bot
   ```

2. Скопируйте содержимое текущего проекта в свежий клон (например, через `rsync` или `cp -r`).

3. Убедитесь, что все необходимые файлы присутствуют:
   - `waterland_bot/bot.py`
   - каталог `waterland_bot/rag/` c индексами и метаданными
   - каталог `waterland_bot/reports/`
   - каталог `waterland_bot/utils/`
   - `waterland_bot/requirements.txt`
   - `waterland_bot/README.md`
   - корневой `README.md`
   - новые служебные файлы `sessions/`, `logs/`, `prompts/` (директории можно создать пустыми)

4. Проверьте статус git:
   ```bash
   git status
   ```

5. Зафиксируйте изменения:
   ```bash
   git add .
   git commit -m "Deploy Viva WaterLand Assistant bot"
   ```

6. Установите удалённый upstream (если ещё не настроен) и отправьте изменения:
   ```bash
   git remote add origin git@github.com:Adrukla-WL/TG-bot.git  # пропустите, если уже задан
   git push origin main  # или нужная ветка
   ```

7. Убедитесь, что все файлы появились на GitHub.

> **Примечание:** текущая среда выполнения не имеет доступа к вашим GitHub-учётным данным, поэтому фактическая отправка (`git push`) должна выполняться с машины, где настроена аутентификация.
