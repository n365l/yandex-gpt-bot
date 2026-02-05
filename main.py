import os
import telebot
import requests
from flask import Flask, request
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные окружения (Railway сам их подставит)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
FOLDER_ID = os.environ.get("FOLDER_ID", "b1gnqesu7v521unserv8")

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Создаем Flask приложение (для вебхука)
app = Flask(__name__)

# Хранилище истории (в памяти, для Railway можно использовать Redis)
user_histories = {}

def ask_yandex_gpt_with_history(user_id, text):
    """Запрос к Yandex GPT с историей диалога"""
    
    # Инициализируем историю для пользователя
    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "text": "Ты — полезный и дружелюбный помощник в Telegram. У тебя есть память о предыдущих сообщениях. Отвечай кратко и по делу."}
        ]
    
    # Добавляем новый вопрос
    user_histories[user_id].append({"role": "user", "text": text})
    
    # Ограничиваем историю (последние 10 сообщений)
    if len(user_histories[user_id]) > 20:  # 1 системное + 19 диалога
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-19:]
    
    # Формируем запрос
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
        "messages": user_histories[user_id]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            ai_reply = result["result"]["alternatives"][0]["message"]["text"]
            
            # Добавляем ответ ассистента в историю
            user_histories[user_id].append({"role": "assistant", "text": ai_reply})
            
            return ai_reply
        else:
            logger.error(f"Yandex GPT ошибка: {response.status_code}")
            return "Извините, сервис временно недоступен."
            
    except Exception as e:
        logger.error(f"Ошибка подключения: {e}")
        return "Ошибка соединения с ИИ."

# Обработчики команд
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_histories[user_id] = []  # Очищаем историю
    bot.reply_to(message, "👋 Привет! Я ИИ-бот с памятью о нашем разговоре!\nПросто напиши мне что-нибудь.")

@bot.message_handler(commands=['clear'])
def clear_command(message):
    user_id = message.from_user.id
    user_histories[user_id] = []
    bot.reply_to(message, "🧹 История диалога очищена!")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🆘 *Помощь по командам:*

/start - начать диалог (очистить историю)
/clear - очистить историю разговора
/help - это сообщение

Бот помнит последние 10 сообщений в разговоре!
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    logger.info(f"Сообщение от {user_id}: {message.text[:50]}...")
    
    # Показываем "печатает..."
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Получаем ответ с историей
    reply = ask_yandex_gpt_with_history(user_id, message.text)
    
    # Отправляем ответ
    bot.reply_to(message, reply)
    logger.info(f"Отправлен ответ пользователю {user_id}")

# Вебхук для Railway
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.

process_new_updates([update])
        return 'OK', 200
    else:
        return 'Bad Request', 400

@app.route('/')
def index():
    return '🤖 Бот работает!'

# Запуск через веб-сервер (для Railway)
if __name__ == '__main__':
    # Удаляем старые вебхуки
    bot.remove_webhook()
    
    # Устанавливаем вебхук (Railway даст свой URL)
    railway_url = os.environ.get("RAILWAY_STATIC_URL")
    if railway_url:
        bot.set_webhook(url=f"{railway_url}/webhook")
        logger.info(f"Вебхук установлен: {railway_url}/webhook")
    
    # Запускаем Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)