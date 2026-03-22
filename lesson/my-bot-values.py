import requests

url = "https://www.cbr-xml-daily.ru/daily_json.js"

# 1. Получаем данные с сайта
response = requests.get(url)
data = response.json()

# 2. Пользователь вводит валюту
currency_code = input("Введите код валюты (например, USD, EUR): ").upper()

# 3. Проверяем, есть ли такая валюта
valutes = data["Valute"]

if currency_code in valutes:
    currency = valutes[currency_code]
    name = currency["Name"]
    value = currency["Value"]
    nominal = currency["Nominal"]

    print(f"{nominal} {name} = {value} рублей")
else:
    print("Такой валюты нет в данных ЦБ")
