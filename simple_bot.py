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

# ----- Логи -----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- Flask -----
app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": "*"}})

# ----- ENV -----
TOKEN_1 = os.environ.get('TELEGRAM_BOT_TOKEN_1')
TOKEN_2 = os.environ.get('TELEGRAM_BOT_TOKEN_2')

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
GAS_URL = "https://script.google.com/macros/s/AKfycbzc6t6LGck4FxCNO8Ayggoa5LNBOSne3JBPdPW8I7z4dFpAyTZb9G6iPkLJTVGtIOCh/exec"

# ----- КЕШ -----
CACHE = {"books": [], "timestamp": 0}
CACHE_TTL = 10

lock = threading.Lock()

# ----- Google Script -----
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
        logger.error(f"GAS GET error: {e}")
        return CACHE["books"]


def save_books(books):
    try:
        r = requests.post(GAS_URL, json={"books": books}, timeout=10)
        if r.status_code != 200:
            return False

        data = r.json()
        return data.get("success") is True

    except Exception as e:
        logger.error(f"GAS POST error: {e}")
        return False


# ----- Telegram -----
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


# ----- Премиум бот -----
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "💎 Премиум режим\n\nСкоро будет оплата и расширенные функции 🚀"
    )


# ----- Flask Routes -----
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/get_ads')
def get_ads():
    books = get_books()
    return jsonify({"books": books})


@app.route('/save_ad', methods=['POST'])
def save_ad():
    try:
        data = request.get_json()

        if not data or 'title' not in data:
            return jsonify({"error": "Invalid data"}), 400

        try:
            price = float(data.get('price', 0))
        except (ValueError, TypeError):
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
        logger.error(f"save_ad error: {e}")
        return jsonify({"error": "server error"}), 500


# ----- Запуск бота -----
def run_bot(token, is_premium=False):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = Application.builder().token(token).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("books", books_command))

    if is_premium:
        bot.add_handler(CommandHandler("premium", premium))

    logger.info(f"🚀 Бот запущен: {'premium' if is_premium else 'main'}")

    bot.run_polling(drop_pending_updates=True)


# ----- Стартуем ботов -----
if os.environ.get("RUN_BOT_1", "true") == "true" and TOKEN_1:
    threading.Thread(target=run_bot, args=(TOKEN_1, False), daemon=True).start()

if os.environ.get("RUN_BOT_2", "false") == "true" and TOKEN_2:
    threading.Thread(target=run_bot, args=(TOKEN_2, True), daemon=True).start()


# ----- Render -----
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
