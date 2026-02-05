import os
import telebot
import requests
from flask import Flask, request

# Создаем Flask приложение
app = Flask(__name__)

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

# Вебхук для Railway
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Bad Request', 400

@app.route('/')
def index():
    return '🤖 Бот работает на Railway!'

# Запуск
if __name__ == "__main__":
    # Устанавливаем вебхук при запуске
    bot.remove_webhook()
    # URL получим после генерации домена
    bot.set_webhook(url="https://yandex-gpt-bot.up.railway.app/webhook")
    
    # Запускаем Flask на порту 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

