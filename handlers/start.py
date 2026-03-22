from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from services.user_service import register_user, set_admin
from services.action_service import log_action
from my_settings import ADMIN_ID

INSTRUCTION_TEXT = (
    "👋 <b>Добро пожаловать!</b>\n\n"
    "Это бот для скачивания видео с <b>Первого канала</b>.\n"
    "Просто отправьте ссылку на видео — я загружу его на Google Drive и пришлю ссылку.\n\n"
    "📌 <b>Как пользоваться:</b>\n"
    "1️⃣ Откройте видео на сайте 1tv.ru\n"
    "2️⃣ Нажмите кнопку «Поделиться»\n"
    "3️⃣ Скопируйте короткую ссылку вида:\n"
    "<code>https://www.1tv.ru/-/***</code>\n\n"
    "✅ Видео будет доступно 24 часа"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Регистрация пользователя
    is_new = register_user(user)
    log_action(user.id, "start")

    # Проверка на админа
    if user.id == ADMIN_ID:
        set_admin(user.id)
        print(f"👑 Админ авторизован: {user.username}")

    # Уведомление о новом пользователе
    if is_new:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆕 Новый пользователь: @{user.username} (id={user.id})"
        )
        print(f"👤 Новый пользователь: {user.username}")

    # Отправка инструкции
    try:
        with open("assets/how_to_copy_link1.jpg", "rb") as img1, \
             open("assets/how_to_copy_link2.jpg", "rb") as img2:

            media = [
                InputMediaPhoto(
                    media=img1,
                    caption=INSTRUCTION_TEXT,
                    parse_mode="HTML"
                ),
                InputMediaPhoto(media=img2)
            ]

            await update.message.reply_media_group(media=media)
            print(f"📨 Инструкция отправлена пользователю {user.id}")

    except FileNotFoundError:
        # Если картинки не найдены — отправляем только текст
        await update.message.reply_text(
            INSTRUCTION_TEXT,
            parse_mode="HTML"
        )
        print(f"⚠️ Картинки инструкции не найдены для {user.id}")