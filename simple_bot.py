import os
import logging
import threading
import asyncio
import uuid
import time
import requests

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не задан")
    exit(1)

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://telegrambot-sbae.onrender.com')
GAS_URL = "https://script.google.com/macros/s/AKfycbzc6t6LGck4FxCNO8Ayggoa5LNBOSne3JBPdPW8I7z4dFpAyTZb9G6iPkLJTVGtIOCh/exec"

CACHE = {"books": [], "timestamp": 0}
CACHE_TTL = 10

lock = threading.Lock()

# ----- DATA -----
def get_books(force=False):
    now = time.time()

    if not force and now - CACHE["timestamp"] < CACHE_TTL:
        return CACHE["books"]

    try:
        r = requests.get(GAS_URL, timeout=10)
        if r.status_code != 200:
            return CACHE["books"]

        data = r.json()
        books = data.get('books', [])

        CACHE["books"] = books
        CACHE["timestamp"] = now

        return books
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки книг: {e}")
        return CACHE["books"]


def save_books(books):
    try:
        r = requests.post(GAS_URL, json={"books": books}, timeout=10)
        if r.status_code != 200:
            return False

        data = r.json()
        # Успешно, если GAS вернул поле "books" или "success": true
        return 'books' in data or data.get('success') is True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения книг: {e}")
        return False


# ----- TELEGRAM -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    keyboard = [[InlineKeyboardButton(
        "📚 Открыть Bookshelf",
        web_app=WebAppInfo(url=RENDER_URL)
    )]]

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\nЖми кнопку 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    books = get_books()

    if not books:
        await update.message.reply_text("📚 Книг пока нет")
        return

    books_sorted = sorted(books, key=lambda x: x.get('date', ''), reverse=True)

    msg = "📚 Последние книги:\n\n"
    for b in books_sorted[:10]:
        msg += f"📖 {b.get('title')} — {b.get('price')} ₽\n"

    await update.message.reply_text(msg)


# ----- FLASK -----
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)


@app.route('/get_ads')
def get_ads():
    return jsonify({"books": get_books()})


@app.route('/save_ad', methods=['POST'])
def save_ad():
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({"error": "Invalid data"}), 400

        try:
            price = float(data.get('price', 0))
        except:
            price = 0

        new_book = {
            "id": str(uuid.uuid4()),
            "title": data.get('title'),
            "author": data.get('author', ''),
            "price": price,
            "contact": data.get('contact', ''),
            "date": __import__('datetime').datetime.utcnow().isoformat()
        }

        with lock:
            books = get_books(force=True)
            books.append(new_book)

            if not save_books(books):
                return jsonify({"error": "save failed"}), 500

            CACHE["books"] = books
            CACHE["timestamp"] = time.time()

        return jsonify({"status": "ok", "book": new_book})

    except Exception as e:
        logger.error(f"❌ save_ad ошибка: {e}")
        return jsonify({"error": "server error"}), 500


# ----- BOT -----
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("books", books_command))

    logger.info("🚀 Бот запущен")
    bot.run_polling(drop_pending_updates=True)


threading.Thread(target=run_bot, daemon=True).start()


# ----- START -----
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
