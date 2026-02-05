import os
import telebot
import requests

# Получаем переменные из окружения Railway
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
FOLDER_ID = os.environ.get("FOLDER_ID", "b1gnqesu7v521unserv8")

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Функция для запроса к Yandex GPT
def ask_yandex_gpt(text):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "temperature": 0.3,
            "maxTokens": 1000
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты — полезный помощник в Telegram. Отвечай кратко и по делу."
            },
            {
                "role": "user",
                "text": text
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result["result"]["alternatives"][0]["message"]["text"]
        else:
            return f"Ошибка: {response.status_code}"
            
    except Exception as e:
        return f"Ошибка соединения: {str(e)}"

# Команда /start
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "🤖 Привет! Я бот в облаке Railway! Просто напиши мне что-нибудь.")

# Обработка всех сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    answer = ask_yandex_gpt(message.text)
    bot.reply_to(message, answer)

# Запуск бота
if __name__ == "__main__":
    print("✅ Бот запускается в Railway...")
    bot.infinity_polling()

