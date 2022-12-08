import os
import telebot
from dotenv import load_dotenv
from flask import (Flask, request, abort)

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
WEBHOOK_URL_BASE = os.getenv('URL_PATH')
WEBHOOK_URL_PATH = API_TOKEN

app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN, threaded=False)


# Bot API view
@app.route('/' + WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

# Custom views
# ...
