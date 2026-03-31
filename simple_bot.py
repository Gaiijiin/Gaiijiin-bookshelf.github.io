import os
import logging
import threading
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============ ПЕРЕМЕННЫЕ ============
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("❌ Нет токена!")
    exit(1)

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://telegrambot-sbae.onrender.com')
GAS_URL = "https://script.google.com/macros/s/AKfycbzc6t6LGck4FxCNO8Ayggoa5LNBOSne3JBPdPW8I7z4dFpAyTZb9G6iPkLJTVGtIOCh/exec"

logger.info(f"✅ URL: {RENDER_URL}")

# ============ РАБОТА С GAS ============
def get_books():
    try:
        r = requests.get(GAS_URL, timeout=10)
        if r.status_code == 200:
            data = r.json()
            books = data.get('books', [])
            logger.info(f"✅ Загружено {len(books)} книг из GAS")
            return books
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return []

def save_books(books):
    try:
        r = requests.post(GAS_URL, json={"books": books}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('success') or 'books' in data:
                logger.info(f"✅ Сохранено {len(books)} книг в GAS")
                return True
        logger.error(f"❌ Ошибка сохранения: {r.status_code}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

# ============ КОМАНДЫ БОТА ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📚 Открыть Bookshelf", web_app=WebAppInfo(url=RENDER_URL))]]
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
    for b in books[-10:]:
        msg += f"📖 {b.get('title', '?')} - {b.get('price', '?')} руб.\n"
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
    books = get_books()
    return jsonify({"status": "ok", "books": len(books)})

@app.route('/save_ad', methods=['POST'])
def save_ad():
    try:
        data = request.get_json()
        logger.info(f"📥 Получено: {data}")
        
        books = get_books()
        
        new_book = {
            "id": len(books) + 1,
            "title": data.get('title', 'Без названия'),
            "author": data.get('author', 'Неизвестен'),
            "price": data.get('price', 0),
            "contact": data.get('contact', ''),
            "date": __import__('datetime').datetime.now().isoformat()
        }
        
        books.append(new_book)
        
        if save_books(books):
            return jsonify({"status": "ok", "book": new_book}), 200
        else:
            return jsonify({"error": "Ошибка сохранения"}), 500
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    books = get_books()
    return jsonify({"books": books, "total": len(books)})

# ============ ЗАПУСК БОТА ============
def run_bot():
    try:
        bot_app = Application.builder().token(TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("books", books_command))
        logger.info("🚀 Бот запущен!")
        bot_app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")

bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

# ============ ЗАПУСК FLASK ============
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
