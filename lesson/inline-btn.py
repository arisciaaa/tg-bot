from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from my_settings import API

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с reply-кнопками для выбора валюты."""
    keyboard = [
        ['RUB', 'USD'],  # Первый ряд кнопок
        ['EUR', 'BTC']  # Второй ряд кнопок
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    # Отправляем сообщение с нашей клавиатурой
    await update.message.reply_text('Пожалуйста, выберите валюту:', reply_markup=reply_markup)


async def handle_currency_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор валюты пользователем."""
    # Получаем текст, отправленный пользователем (например, нажатие на кнопку)
    text = update.message.text
    await update.message.reply_text(f'Вы выбрали валюту: {text}')


def main():
    """Запускает бота."""
    # Замените 'YOUR_TOKEN' на токен вашего бота
    application = Application.builder().token(API).build()

    # Добавляем обработчик команды /start
    application.add_handler(CommandHandler('start', start))

    # Добавляем обработчик для текстовых сообщений, чтобы обрабатывать выбор валюты
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_currency_selection))

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()