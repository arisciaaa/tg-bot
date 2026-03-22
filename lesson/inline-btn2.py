from telegram import (
    Update, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler)
from my_settings import API
import requests

def parse():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"

    response = requests.get(url)
    data = response.json()

    return data

def get_values(data, currency_code: str):

    valutes = data["Valute"]

    if currency_code in valutes:
        currency = valutes[currency_code]
        name = currency["Name"]
        value = currency["Value"]
        nominal = currency["Nominal"]

        return(f"{nominal} {name} = {value} рублей")
    else:
        return(f"Кажется, такой валюты у меня нет(")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с inline-кнопками для выбора валюты."""
    data = parse()

    keyboard = []
    for elem in data['Valute']:
        keyboard.append([InlineKeyboardButton(f"{elem}", callback_data=f"{elem}"), InlineKeyboardButton(f"{elem}", callback_data=f"{elem}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем сообщение с нашей inline-клавиатурой
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Пожалуйста, выберите валюту:',
                                     reply_markup=reply_markup)


async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на inline-кнопки.
    """
    query = update.callback_query
    await query.answer()  # Обязательно отвечаем на callback, чтобы Telegram не "подвисал".

    # Достаем из callback_data название валюты
    chosen_currency = query.data
    await query.message.reply_text(f"Вы выбрали валюту: {chosen_currency}")

    answer = get_values(parse(), chosen_currency)
    await query.message.reply_text(answer)


def main():
    """Запускает бота."""
    # Замените 'YOUR_TOKEN' на токен вашего бота
    application = Application.builder().token(API).build()

    # Добавляем обработчик команды /start
    application.add_handler(CommandHandler('start', start))

    # Обработчик колбэков (нажатий на inline-кнопки)
    application.add_handler(CallbackQueryHandler(handle_inline_buttons))

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()