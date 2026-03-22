import logging
import os
import shutil
import datetime
import asyncio

from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters
)
from telegram.request import HTTPXRequest

from my_settings import API
from services.user_service import init_users_table
from services.action_service import init_actions_table
from handlers.start import start
from handlers.video_handler import handle_message, uploaded_files
from services.google_drive import gdrive_uploader

# Настройка логирования
logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


def cleanup_temp_files():
    """Удаляет все временные видео при запуске бота"""
    temp_dir = "temp_videos"
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            print("🧹 Временные файлы очищены")
        except Exception as e:
            print(f"❌ Ошибка очистки: {e}")


async def cleanup_old_files():
    """Периодически удаляет файлы с Google Drive старше 24 часов"""
    while True:
        try:
            now = datetime.datetime.now()
            to_delete = []

            for file_id, info in uploaded_files.items():
                age = now - info["upload_time"]
                if age.total_seconds() > 24 * 3600:  # 24 часа
                    success = gdrive_uploader.delete_file(file_id)
                    if success:
                        print(f"🗑️ Удалён старый файл: {file_id}")
                        to_delete.append(file_id)

            # Очищаем словарь
            for file_id in to_delete:
                del uploaded_files[file_id]

        except Exception as e:
            print(f"Ошибка при очистке: {e}")

        await asyncio.sleep(3600)  # Проверка каждый час


async def post_init(application):
    """Действия после инициализации бота"""
    asyncio.create_task(cleanup_old_files())
    print("✅ Бот запущен и готов к работе")


def main():
    # Очистка временных файлов
    cleanup_temp_files()

    # Инициализация БД
    init_users_table()
    init_actions_table()

    # Настройка HTTP клиента
    request = HTTPXRequest(connect_timeout=60, read_timeout=60)

    # Создание приложения
    app = ApplicationBuilder().token(API).request(request).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Хуки жизненного цикла
    app.post_init = post_init

    # Запуск
    print("🚀 Запуск бота...")
    app.run_polling()


if __name__ == "__main__":
    main()