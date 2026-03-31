import os
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

# ============ ПЕРЕМЕННЫЕ ============
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("❌ Нет токена!")
    exit(1)

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://telegrambot-sbae.onrender.com')
logger.info(f"✅ Бот запущен: {RENDER_URL}")

# ============ ХРАНИЛИЩЕ КНИГ ============
books = []

# ============ КОМАНДЫ БОТА ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📚 Открыть Bookshelf", web_app=WebAppInfo(url=RENDER_URL))]]
    await update.message.reply_text(
        "👋 Добро пожаловать в Bookshelf!\n\n👇 Нажми на кнопку, чтобы открыть приложение",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"✅ Команда start от {update.effective_user.username}")

async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not books:
        await update.message.reply_text("📚 Книг пока нет")
        return
    msg = "📚 Книги:\n\n"
    for b in books[-10:]:
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
    return jsonify({"status": "ok", "books": len(books)})

@app.route('/save_ad', methods=['POST'])
def save_ad():
    try:
        data = request.get_json()
        logger.info(f"📥 Получено: {data}")
        
        new_book = {
            "id": len(books) + 1,
            "title": data.get('title', 'Без названия'),
            "author": data.get('author', 'Неизвестен'),
            "price": data.get('price', 0),
            "contact": data.get('contact', ''),
            "date": __import__('datetime').datetime.now().isoformat()
        }
        
        books.append(new_book)
        logger.info(f"✅ Книга сохранена: {new_book['title']}")
        return jsonify({"status": "ok", "book": new_book}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    return jsonify({"books": books, "total": len(books)})

# ============ ЗАПУСК FLASK В ОТДЕЛЬНОМ ПОТОКЕ ============
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# ============ ЗАПУСК БОТА В ГЛАВНОМ ПОТОКЕ ============
def run_bot():
    try:
        # Создаем приложение
        bot_app = Application.builder().token(TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("books", books_command))
        
        logger.info("🚀 Запуск бота...")
        # Запускаем polling (блокирует поток)
        bot_app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")

# ============ ЗАПУСК ============
if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🚀 Flask запущен в фоне")
    
    # Запускаем бота в главном потоке
    run_bot()
