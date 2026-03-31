import os
import re
import logging
import asyncio
import requests
import json
import threading
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# ============ НАСТРОЙКА ============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============ ФУНКЦИЯ ОЧИСТКИ URL ============
def clean_url(url: str) -> str:
    if not url:
        return url
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', url)
    return cleaned.strip()

# ============ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ============
TOKEN = clean_url(os.environ.get('TELEGRAM_BOT_TOKEN', ''))
if not TOKEN:
    logger.error("❌ Нет токена!")
    exit(1)

RENDER_URL = clean_url(os.environ.get('RENDER_EXTERNAL_URL', 'https://telegrambot-sbae.onrender.com'))
logger.info(f"✅ Бот запущен: {RENDER_URL}")

# ============ KEEP-ALIVE ============
def keep_alive():
    while True:
        time.sleep(240)
        try:
            requests.get(f"https://{RENDER_URL}", timeout=10)
            logger.info("🏓 Keep-alive ping")
        except:
            pass

if "localhost" not in RENDER_URL:
    ping_thread = threading.Thread(target=keep_alive, daemon=True)
    ping_thread.start()
    logger.info("🔄 Keep-alive активирован")

# ============ КОНСТАНТЫ ============
GAS_URL = "https://script.google.com/macros/s/AKfycbzc6t6LGck4FxCNO8Ayggoa5LNBOSne3JBPdPW8I7z4dFpAyTZb9G6iPkLJTVGtIOCh/exec"

# ============ РАБОТА С GAS ============
def get_books():
    try:
        r = requests.get(GAS_URL, timeout=10)
        if r.status_code == 200:
            data = r.json()
            books = data.get('books', [])
            logger.info(f"✅ Загружено {len(books)} книг")
            return books
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return []

def save_books(books):
    try:
        r = requests.post(GAS_URL, json={"books": books}, timeout=10)
        if r.status_code == 200 and r.json().get('success'):
            logger.info(f"✅ Сохранено {len(books)} книг")
            return True
        logger.error(f"❌ Ошибка сохранения: {r.status_code}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

def add_book(title, author, price, contact):
    books = get_books()
    new_book = {
        "id": len(books) + 1,
        "title": title,
        "author": author,
        "price": price,
        "contact": contact,
        "date": __import__('datetime').datetime.now().isoformat()
    }
    books.append(new_book)
    if save_books(books):
        return True, new_book
    return False, None

# ============ КОМАНДЫ БОТА ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📚 Открыть", web_app=WebAppInfo(url=RENDER_URL))]]
    await update.message.reply_text(
        "👋 Добро пожаловать в Bookshelf!\n\n👇 Нажми на кнопку",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    books = get_books()
    if not books:
        await update.message.reply_text("📚 Книг пока нет")
        return
    msg = "📚 Книги:\n\n"
    for b in books[-5:]:
        msg += f"📖 {b.get('title')} - {b.get('price')} руб.\n"
    await update.message.reply_text(msg)

# ============ FLASK МАРШРУТЫ ============
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def css():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def js():
    return send_from_directory('.', 'script.js')

@app.route('/health')
def health():
    return jsonify({"status": "ok", "books": len(get_books())})

@app.route('/save_ad', methods=['POST', 'OPTIONS'])
def save_ad():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        logger.info(f"📥 Получено: {data}")
        
        title = data.get('title')
        if not title:
            return jsonify({"error": "Название обязательно"}), 400
        
        success, book = add_book(
            title,
            data.get('author', 'Неизвестен'),
            data.get('price', 0),
            data.get('contact', '')
        )
        
        if success:
            return jsonify({"status": "ok", "book": book}), 200
        return jsonify({"error": "Ошибка сохранения"}), 500
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    return jsonify({"books": get_books()})

@app.route('/webhook', methods=['POST'])
def webhook():
    global bot_app
    if not bot_app:
        return jsonify({"error": "Bot not ready"}), 500
    
    try:
        data = request.json
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        update = Update.de_json(data, bot_app.bot)
        loop.run_until_complete(bot_app.process_update(update))
        loop.close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"❌ Webhook: {e}")
        return jsonify({"error": str(e)}), 500

# ============ ЗАПУСК БОТА ============
bot_app = None

def setup():
    global bot_app
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("books", books_command))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_app.initialize())
    loop.run_until_complete(bot_app.bot.set_webhook(
        url=f"{RENDER_URL}/webhook",
        timeout=60  # увеличиваем таймаут
    ))
    loop.close()
    logger.info("✅ Бот готов!")

# ============ ЗАПУСК ============
if __name__ == "__main__":
    setup()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
