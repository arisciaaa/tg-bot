from telegram import Update
from telegram.ext import ContextTypes
from services.action_service import log_action
from services.downloader import get_video_info, download_video_with_progress
from services.google_drive import gdrive_uploader
import re
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import datetime
import time

# Хранилище данных
uploaded_files = {}  # для автоудаления
busy_users = set()   # занятые пользователи
executor = ThreadPoolExecutor(max_workers=2)  # меньше потоков = стабильнее

QUALITY_NAMES = {
    'hd': '📺 Высокое (HD)',
    'sd': '📱 Среднее (SD)',
    'ld': '📟 Низкое (LD)'
}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    start_time = time.time()

    print(f"\n📨 [ПОЛЬЗОВАТЕЛЬ {user.id}] Сообщение: {text[:50]}...")
    log_action(user.id, f"message: {text[:50]}...")

    # Проверка на занятость
    if user.id in busy_users:
        await update.message.reply_text(
            "⏳ <b>Я уже обрабатываю твоё видео!</b>\n\n"
            "Оно загружается в фоне. Когда видео будет готово — я пришлю его сюда.",
            parse_mode="HTML"
        )
        return

    # Проверка ссылки
    if not is_1tv_link(text):
        await update.message.reply_text(
            "Отправьте ссылку на видео с сайта 1tv.ru\n"
            "Например: https://www.1tv.ru/-/abc123"
        )
        return

    # Получаем информацию о видео
    status_msg = await update.message.reply_text(
        "🔍 <b>Получаю информацию о видео...</b>",
        parse_mode="HTML"
    )

    print(f"🌐 Получаю информацию для URL: {text}")
    video_info = get_video_info(text)

    if not video_info or not video_info.get('video_url'):
        await status_msg.edit_text(
            "❌ Не удалось получить информацию о видео.\n"
            "Проверьте ссылку или попробуйте позже."
        )
        print(f"❌ Ошибка: не удалось получить video_info")
        return

    # Помечаем пользователя как занятого
    busy_users.add(user.id)
    print(f"👤 Пользователь {user.id} добавлен в busy_users")

    await status_msg.edit_text(
        f"🎬 <b>{video_info['title']}</b>\n\n"
        f"⏬ Видео добавлено в очередь на загрузку!\n"
        f"Это займёт какое-то время. Я буду писать о прогрессе ☕",
        parse_mode="HTML"
    )

    # Запускаем фоновую задачу
    asyncio.create_task(
        process_video_task(
            user_id=user.id,
            video_url=video_info['video_url'],
            video_title=video_info['title'],
            context=context,
            start_time=start_time
        )
    )


async def process_video_task(user_id, video_url, video_title, context, start_time):
    """Фоновая задача: скачать видео и загрузить на Google Drive"""
    status_message = None
    filename = None

    try:
        # Создаём папку для временных файлов
        temp_dir = "temp_videos"
        os.makedirs(temp_dir, exist_ok=True)

        filename = os.path.join(temp_dir, f"video_{user_id}_{int(time.time())}.mp4")
        print(f"📁 Будет сохранено в: {filename}")

        # Отправляем первое сообщение о прогрессе
        status_message = await context.bot.send_message(
            chat_id=user_id,
            text="⏳ <b>Начинаю скачивание видео...</b>\n\n"
                 "0% [░░░░░░░░░░░░░░░░░░░░] 0 MB",
            parse_mode="HTML"
        )

        # Функция для обновления прогресса скачивания
        async def progress_callback(current, total, percent):
            if status_message:
                # Визуальный прогресс-бар (20 символов)
                filled = int(percent // 5)
                bar = "█" * filled + "░" * (20 - filled)

                text = (f"⏳ <b>Скачиваю видео</b>\n\n"
                        f"{bar} {percent:.1f}%\n"
                        f"📦 {current // (1024 * 1024)} / {total // (1024 * 1024)} MB")

                try:
                    await context.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=status_message.message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"⚠️ Ошибка обновления: {e}")

        # Скачиваем видео с прогрессом
        print(f"⬇️ Начинаю скачивание для пользователя {user_id}")
        success = await download_video_with_progress(
            video_url=video_url,
            save_path=filename,
            progress_callback=progress_callback
        )

        if not success or not os.path.exists(filename):
            raise Exception("Не удалось скачать видео")

        file_size = os.path.getsize(filename) / (1024 * 1024)
        print(f"✅ Видео скачано: {file_size:.1f} MB")

        # Обновляем статус
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=status_message.message_id,
            text="☁️ <b>Загружаю на Google Drive...</b>\n\n"
                 f"Размер: {file_size:.1f} MB\n"
                 "Это может занять 1-2 минуты.",
            parse_mode="HTML"
        )

        # Загружаем на Google Drive
        print(f"☁️ Загружаю на Google Drive...")
        loop = asyncio.get_event_loop()
        file_id, view_link, download_link = await loop.run_in_executor(
            executor,
            lambda: gdrive_uploader.upload_file(
                filename,
                f"video_{video_title[:30]}.mp4"
            )
        )

        # Сохраняем для автоудаления
        uploaded_files[file_id] = {
            "user_id": user_id,
            "upload_time": datetime.datetime.now(),
            "view_link": view_link,
            "download_link": download_link
        }

        # Финальное сообщение
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=status_message.message_id,
            text=f"✅ <b>Видео готово!</b>\n\n"
                 f"🎬 {video_title}\n"
                 f"📦 Размер: {file_size:.1f} MB\n\n"
                 f"🔗 <b>Ссылка для просмотра:</b>\n"
                 f"{view_link}\n\n"
                 f"⬇️ <b>Прямая ссылка:</b>\n"
                 f"{download_link}\n\n"
                 f"⏳ <i>Файл будет удалён через 24 часа</i>",
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        print(f"✅ Видео отправлено пользователю {user_id}")
        print(f"⏱️  Время обработки: {time.time() - start_time:.1f} сек")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if status_message:
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=status_message.message_id,
                text="❌ <b>Произошла ошибка</b>\n\n"
                     "Попробуйте позже или выберите другое видео.",
                parse_mode="HTML"
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Не удалось обработать видео. Попробуйте позже."
            )

    finally:
        # Освобождаем пользователя
        busy_users.discard(user_id)
        print(f"👤 Пользователь {user_id} освобождён")

        # Удаляем локальный файл
        if filename and os.path.exists(filename):
            os.remove(filename)
            print(f"🗑️ Локальный файл удалён")


def is_1tv_link(text: str) -> bool:
    """Проверяет, является ли текст ссылкой на 1tv.ru"""
    if not text:
        return False

    text = text.lower().strip()
    patterns = [
        r'https?://(www\.)?1tv\.ru',
        r'1tv\.ru',
        r'www\.1tv\.ru',
    ]

    return any(re.search(pattern, text) for pattern in patterns)