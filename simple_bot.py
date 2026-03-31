import os
import re
import logging
import asyncio
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# ============ НАСТРОЙКА ============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============ ОЧИСТКА URL ============
def clean_url(url):
    if not url:
        return url
    return re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', url).strip()

# ============ ПЕРЕМЕННЫЕ ============
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("❌ Нет токена!")
    exit(1)

RENDER_URL = clean_url(os.environ.get('RENDER_EXTERNAL_URL', 'https://telegrambot-sbae.onrender.com'))
logger.info(f"✅ URL: {RENDER_URL}")

# ============ ХРАНИЛИЩЕ КНИГ ============
books_db = []

# ============ КОМАНДЫ БОТА ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📚 Открыть Bookshelf", web_app=WebAppInfo(url=RENDER_URL))]]
    await update.message.reply_text(
        "👋 Добро пожаловать в Bookshelf!\n\n👇 Нажми на кнопку ниже",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not books_db:
        await update.message.reply_text("📚 Книг пока нет")
        return
    msg = "📚 Книги:\n\n"
    for b in books_db[-10:]:
        msg += f"📖 {b['title']} - {b['price']} руб.\n"
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
    return jsonify({"status": "ok", "books": len(books_db)})

@app.route('/save_ad', methods=['POST'])
def save_ad():
    try:
        data = request.get_json()
        logger.info(f"📥 Получено: {data}")
        
        title = data.get('title')
        if not title:
            return jsonify({"error": "Название обязательно"}), 400
        
        new_book = {
            "id": len(books_db) + 1,
            "title": title,
            "author": data.get('author', 'Неизвестен'),
            "price": data.get('price', 0),
            "contact": data.get('contact', ''),
            "date": __import__('datetime').datetime.now().isoformat()
        }
        
        books_db.append(new_book)
        logger.info(f"✅ Сохранено: {title}")
        
        return jsonify({"status": "ok", "book": new_book}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    return jsonify({"books": books_db, "total": len(books_db)})

# ============ ЗАПУСК БОТА (С ПРАВИЛЬНЫМ EVENT LOOP) ============
def run_bot():
    """Запускает бота с polling в правильном event loop"""
    try:
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Создаем приложение
        bot_app = Application.builder().token(TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("books", books_command))
        
        logger.info("🚀 Запуск бота с polling...")
        # Запускаем polling (работает в текущем loop)
        bot_app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")

# Запускаем бота в отдельном потоке
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

# ============ ЗАПУСК FLASK ============
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)
