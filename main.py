import telebot
import requests
from flask import Flask, request
from threading import Thread

app = Flask(__name__)

# ========== ВАШИ КЛЮЧИ ПРЯМО В КОДЕ ==========
TELEGRAM_TOKEN = "8296790244:AAEu-Bi5ZA7AwQAjyeAHL2kMcS4mrLwFR5U"
YANDEX_API_KEY = "AQVN0Rbj9WArAG5JyZtynrC6o9RkEw2fIIZVsHsZ"
FOLDER_ID = "b1gnqesu7v521unserv8"
# =============================================

print("=" * 60)
print("🚀 ЗАПУСК БОТА В REPLIT")
print(f"TELEGRAM_TOKEN: {'✅' if TELEGRAM_TOKEN else '❌'}")
print(f"YANDEX_API_KEY: {'✅' if YANDEX_API_KEY else '❌'}")
print("=" * 60)

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def ask_yandex_gpt(text):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}"}
    
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {"temperature": 0.3, "maxTokens": 1000},
        "messages": [
            {"role": "system", "text": "Ты полезный помощник."},
            {"role": "user", "text": text}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()["result"]["alternatives"][0]["message"]["text"]
        return f"Ошибка: {response.status_code}"
    except Exception as e:
        return f"Ошибка: {str(e)}"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🤖 Привет! Я бот на Replit!")

@bot.message_handler(func=lambda m: True)
def reply(m):
    bot.send_chat_action(m.chat.id, 'typing')
    answer = ask_yandex_gpt(m.text)
    bot.reply_to(m, answer)

@app.route('/')
def home():
    return '🤖 Бот работает!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

# Запускаем бота в отдельном потоке
def run_bot():
    bot.infinity_polling()

if name == "__main__":
    # Запускаем бота в фоне
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask сервер
    port = 5000
    print(f"🌐 Веб-сервер запускается на порту {port}")
    app.run(host='0.0.0.0', port=port)

