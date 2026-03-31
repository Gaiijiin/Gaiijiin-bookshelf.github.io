import os
import re
import logging
import asyncio
import requests
import json
from flask import Flask, request, jsonify, send_from_directory
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============ НАСТРОЙКА ============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============ КОНСТАНТЫ ============
GAS_URL = "https://script.google.com/macros/s/AKfycbzc6t6LGck4FxCNO8Ayggoa5LNBOSne3JBPdPW8I7z4dFpAyTZb9G6iPkLJTVGtIOCh/exec"

def clean_url(url: str) -> str:
    if not url:
        return url
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', url)
    return cleaned.strip()

# ============ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ============
TOKEN = clean_url(os.environ.get('TELEGRAM_BOT_TOKEN'))
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
    exit(1)

RENDER_URL = clean_url(os.environ.get('RENDER_EXTERNAL_URL'))
if not RENDER_URL:
    service_name = clean_url(os.environ.get('RENDER_SERVICE_NAME', 'telegrambot-sbae'))
    RENDER_URL = f"https://{service_name}.onrender.com"

logger.info(f"✅ Бот запущен: {RENDER_URL}")

# ============ РАБОТА С GAS ============
def get_books_from_gas():
    try:
        response = requests.get(GAS_URL, timeout=30)
        if response.status_code == 200 and response.text:
            data = response.json()
            books = data.get('books', []) if isinstance(data, dict) else data if isinstance(data, list) else []
            logger.info(f"✅ Загружено {len(books)} книг")
            return books
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка GAS: {e}")
        return []

def save_books_to_gas(books_list):
    try:
        response = requests.post(GAS_URL, json={"books": books_list}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Сохранено {len(books_list)} книг")
                return True
        logger.error(f"❌ Ошибка сохранения: {response.status_code}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

def add_book_to_gas(title, author, price, description, contact):
    books = get_books_from_gas()
    new_book = {
        "id": len(books) + 1,
        "title": title,
        "author": author,
        "price": price,
        "description": description,
        "contact": contact,
        "created_at": __import__('datetime').datetime.now().isoformat()
    }
    books.append(new_book)
    if save_books_to_gas(books):
        return True, new_book
    return False, None

# ============ КОМАНДЫ БОТА ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [[InlineKeyboardButton("📚 Открыть Bookshelf", web_app=WebAppInfo(url=RENDER_URL))]]
        books_count = len(get_books_from_gas())
        await update.message.reply_text(
            f"👋 Добро пожаловать в Bookshelf!\n\n📚 В базе {books_count} книг\n\n👇 Нажми на кнопку ниже",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"❌ Ошибка в start: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("/start - Открыть приложение\n/books - Список книг\n/help - Помощь")
    except Exception as e:
        logger.error(f"❌ Ошибка в help: {e}")

async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        books = get_books_from_gas()
        if not books:
            await update.message.reply_text("📚 Книг пока нет")
            return
        message = "📚 Последние книги:\n\n"
        for book in books[-5:]:
            message += f"📖 {book.get('title', '?')} - {book.get('price', '?')} руб.\n"
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"❌ Ошибка в books: {e}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(f"Я получил: {update.message.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка в echo: {e}")

# ============ FLASK МАРШРУТЫ ============
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def serve_css():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('.', 'script.js')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "books_count": len(get_books_from_gas())})

@app.route('/save_ad', methods=['POST'])
def save_ad():
    try:
        data = request.get_json()
        if not data.get('title'):
            return jsonify({"error": "Название обязательно"}), 400
        
        success, book = add_book_to_gas(
            data.get('title'),
            data.get('author', 'Не указан'),
            data.get('price', 'Не указана'),
            data.get('description', ''),
            data.get('contact', '')
        )
        return jsonify({"status": "ok", "book": book}) if success else jsonify({"error": "Ошибка"}), 500
    except Exception as e:
        logger.error(f"❌ Ошибка save_ad: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    return jsonify({"books": get_books_from_gas(), "total": len(get_books_from_gas())})

@app.route('/webhook', methods=['POST'])
def webhook():
    global bot_app
    if not bot_app:
        return jsonify({"error": "Bot not ready"}), 500
    
    try:
        json_data = request.get_json(force=True)
        if not json_data:
            return jsonify({"error": "No data"}), 400
        
        # СОЗДАЕМ НОВЫЙ EVENT LOOP ДЛЯ КАЖДОГО ЗАПРОСА
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            update = Update.de_json(json_data, bot_app.bot)
            # ЗАПУСКАЕМ И ДОЖИДАЕМСЯ
            loop.run_until_complete(bot_app.process_update(update))
        except RuntimeError as e:
            logger.error(f"❌ RuntimeError в webhook: {e}")
            # Пробуем еще раз с новым loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            update = Update.de_json(json_data, bot_app.bot)
            loop.run_until_complete(bot_app.process_update(update))
        finally:
            loop.close()
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ============ ИНИЦИАЛИЗАЦИЯ БОТА ============
bot_app = None

def setup_bot():
    global bot_app
    logger.info("🔧 Настройка бота...")
    
    # СОЗДАЕМ ПОСТОЯННЫЙ EVENT LOOP
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CommandHandler("books", books_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # ИНИЦИАЛИЗИРУЕМ
    loop.run_until_complete(bot_app.initialize())
    
    # УСТАНАВЛИВАЕМ WEBHOOK
    webhook_url = f"{RENDER_URL}/webhook"
    loop.run_until_complete(bot_app.bot.set_webhook(webhook_url))
    logger.info(f"✅ Webhook установлен: {webhook_url}")
    
    # НЕ ЗАКРЫВАЕМ LOOP ЗДЕСЬ!
    logger.info("🤖 Бот готов!")

# ============ ЗАПУСК ============
if __name__ == "__main__":
    setup_bot()
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск на порту {port}")
    app.run(host='0.0.0.0', port=port)
