import os
import re
import logging
import asyncio
import requests
import json
import threading
import time
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

# ============ KEEP-ALIVE ============
def keep_alive():
    while True:
        time.sleep(240)
        try:
            requests.get(f"https://{RENDER_URL}", timeout=10)
            logger.info("🏓 Keep-alive ping")
        except:
            pass

if RENDER_URL and "localhost" not in RENDER_URL:
    ping_thread = threading.Thread(target=keep_alive, daemon=True)
    ping_thread.start()
    logger.info("🔄 Keep-alive активирован")

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
        logger.error(f"❌ Ошибка GAS GET: {e}")
        return []

def save_books_to_gas(books_list):
    try:
        logger.info(f"📤 Отправка в GAS {len(books_list)} книг")
        payload = {"books": books_list}
        response = requests.post(GAS_URL, json=payload, timeout=30)
        logger.info(f"📡 GAS ответ: статус {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"📡 GAS результат: {result}")
            if result.get('success'):
                logger.info(f"✅ Сохранено {len(books_list)} книг в GAS")
                return True
            else:
                logger.error(f"❌ GAS ошибка: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ GAS HTTP ошибка: {response.status_code}")
            logger.error(f"❌ Ответ: {response.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения в GAS: {e}")
        return False

def add_book_to_gas(title, author, price, description, contact):
    logger.info(f"📝 Добавление книги: {title}")
    books = get_books_from_gas()
    
    new_book = {
        "id": len(books) + 1,
        "title": title,
        "author": author,
        "genre": "другое",
        "condition": "хорошее",
        "price": int(price),
        "contact": contact,
        "sellerName": contact,
        "description": description,
        "created_at": __import__('datetime').datetime.now().isoformat()
    }
    
    books.append(new_book)
    
    if save_books_to_gas(books):
        logger.info(f"✅ Книга сохранена: {title}")
        return True, new_book
    else:
        logger.error(f"❌ Не удалось сохранить книгу: {title}")
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
    response = send_from_directory('.', 'index.html')
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

@app.route('/style.css')
def serve_css():
    response = send_from_directory('.', 'style.css')
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response

@app.route('/script.js')
def serve_js():
    response = send_from_directory('.', 'script.js')
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "books_count": len(get_books_from_gas())})

@app.route('/save_ad', methods=['POST'])
def save_ad():
    try:
        data = request.get_json()
        logger.info(f"📥 Получен запрос /save_ad: {data}")
        
        if not data:
            logger.error("❌ Нет данных в запросе")
            return jsonify({"error": "Нет данных"}), 400
            
        title = data.get('title')
        if not title:
            logger.error("❌ Нет названия книги")
            return jsonify({"error": "Название обязательно"}), 400
        
        author = data.get('author', 'Не указан')
        price = data.get('price', 0)
        description = data.get('description', '')
        contact = data.get('contact', '')
        
        logger.info(f"📚 Сохраняем книгу: {title}, {author}, {price}")
        
        success, book = add_book_to_gas(title, author, price, description, contact)
        
        if success:
            logger.info(f"✅ Книга успешно сохранена: {book}")
            return jsonify({"status": "ok", "message": "Книга добавлена", "book": book}), 200
        else:
            logger.error(f"❌ Ошибка сохранения книги")
            return jsonify({"error": "Ошибка сохранения в GAS"}), 500
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в save_ad: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    try:
        books = get_books_from_gas()
        return jsonify({"books": books, "total": len(books)}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка get_ads: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    global bot_app
    if not bot_app:
        return jsonify({"error": "Bot not ready"}), 500
    
    try:
        json_data = request.get_json(force=True)
        if not json_data:
            return jsonify({"error": "No data"}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
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
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot_app = Application.builder().token(TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CommandHandler("books", books_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    loop.run_until_complete(bot_app.initialize())
    loop.run_until_complete(bot_app.bot.set_webhook(f"{RENDER_URL}/webhook"))
    logger.info(f"✅ Webhook установлен: {RENDER_URL}/webhook")
    
    logger.info("🤖 Бот готов!")

# ============ ЗАПУСК ============
if __name__ == "__main__":
    setup_bot()
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)
