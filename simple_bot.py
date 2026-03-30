import os
import re
import logging
import asyncio
import requests
import json
from flask import Flask, request, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# URL твоего Google Apps Script
GAS_URL = "https://script.google.com/macros/s/AKfycbzvg08q_MxKeivLR8BqCMt5feZpKPJcbaw6Y2_jDbaAM0SmViYB2t4SBtZTkK_xkweH/exec"

def clean_url(url: str) -> str:
    """Очищает URL от непечатных символов"""
    if not url:
        return url
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', url)
    return cleaned.strip()

# Получение переменных окружения
TOKEN_raw = os.environ.get('TELEGRAM_BOT_TOKEN')
TOKEN = clean_url(TOKEN_raw) if TOKEN_raw else None

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
    exit(1)

RENDER_URL_raw = os.environ.get('RENDER_EXTERNAL_URL')
RENDER_URL = clean_url(RENDER_URL_raw) if RENDER_URL_raw else None

if not RENDER_URL:
    service_name_raw = os.environ.get('RENDER_SERVICE_NAME')
    if service_name_raw:
        service_name = clean_url(service_name_raw)
        RENDER_URL = f"https://{service_name}.onrender.com"
    else:
        RENDER_URL = "https://telegrambot-sbae.onrender.com"

RENDER_URL = clean_url(RENDER_URL)
logger.info(f"✅ Бот запущен на URL: {RENDER_URL}")

# ============ ФУНКЦИИ ДЛЯ РАБОТЫ С GOOGLE APPS SCRIPT ============

def get_books_from_gas():
    """Получает список книг из Google Apps Script"""
    try:
        response = requests.get(GAS_URL, timeout=30)
        if response.status_code == 200:
            data = response.json()
            books = data.get('books', [])
            logger.info(f"📚 Загружено книг: {len(books)}")
            return books
        else:
            logger.error(f"Ошибка GAS GET: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"❌ Ошибка получения книг: {e}")
        return []

def save_books_to_gas(books_list):
    """Сохраняет список книг в Google Apps Script"""
    try:
        payload = json.dumps({"books": books_list})
        headers = {'Content-Type': 'application/json'}
        response = requests.post(GAS_URL, data=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Сохранено {len(books_list)} книг в GAS")
                return True
            else:
                logger.error(f"❌ GAS ошибка: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        return False

def add_book_to_gas(title, author, price, description, contact):
    """Добавляет одну книгу в хранилище"""
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

# ============ ОБРАБОТЧИКИ КОМАНД ТЕЛЕГРАМ ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет кнопку с мини-приложением"""
    webapp_url = RENDER_URL
    
    keyboard = [[InlineKeyboardButton(
        text="📚 Открыть Bookshelf", 
        web_app=WebAppInfo(url=webapp_url)
    )]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Показываем статистику
    books = get_books_from_gas()
    books_count = len(books)
    
    await update.message.reply_text(
        f"👋 Добро пожаловать в Bookshelf!\n\n"
        f"📚 В базе {books_count} книг\n\n"
        f"📖 Продавай и покупай книги\n\n"
        f"👇 Нажми на кнопку ниже, чтобы открыть мини-приложение",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    await update.message.reply_text(
        "📚 Bookshelf Bot\n\n"
        "📌 Команды:\n"
        "/start - Открыть мини-приложение\n"
        "/books - Показать все книги\n"
        "/help - Помощь\n\n"
        "📖 Создавай объявления о продаже книг\n"
        "🔍 Находи книги, которые хочешь купить"
    )

async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список всех книг"""
    books = get_books_from_gas()
    
    if not books:
        await update.message.reply_text("📚 Пока нет ни одной книги. Добавь первую через мини-приложение!")
        return
    
    message = "📚 Список книг:\n\n"
    for book in books[-10:]:  # Показываем последние 10
        message += f"📖 {book.get('title', 'Без названия')}\n"
        message += f"💰 {book.get('price', 'Цена не указана')} руб.\n"
        message += f"👤 {book.get('author', 'Автор не указан')}\n"
        message += "➖" * 10 + "\n"
    
    message += f"\nВсего книг: {len(books)}"
    await update.message.reply_text(message)

# ============ FLASK МАРШРУТЫ ДЛЯ МИНИ-ПРИЛОЖЕНИЯ ============

@app.route('/')
def index():
    """Главная страница API"""
    books = get_books_from_gas()
    return jsonify({
        "status": "ok",
        "message": "Bookshelf Bot API",
        "books_count": len(books)
    }), 200

@app.route('/health')
def health():
    """Проверка здоровья"""
    return jsonify({
        "status": "healthy",
        "bot_active": True,
        "gas_connected": True
    }), 200

@app.route('/save_ad', methods=['POST'])
def save_ad():
    """Сохранение объявления через Google Apps Script"""
    try:
        data = request.get_json()
        logger.info(f"📝 Получено объявление: {data}")
        
        # Валидация
        title = data.get('title')
        if not title:
            return jsonify({"error": "Название книги обязательно"}), 400
        
        author = data.get('author', 'Не указан')
        price = data.get('price', 'Не указана')
        description = data.get('description', '')
        contact = data.get('contact', '')
        
        # Сохраняем через GAS
        success, new_book = add_book_to_gas(title, author, price, description, contact)
        
        if success:
            logger.info(f"✅ Книга сохранена: {title}")
            return jsonify({
                "status": "ok",
                "message": "Книга добавлена в библиотеку",
                "book": new_book
            }), 200
        else:
            return jsonify({"error": "Ошибка сохранения в GAS"}), 500
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    """Получение всех книг"""
    try:
        books = get_books_from_gas()
        return jsonify({
            "status": "ok",
            "books": books,
            "total": len(books)
        }), 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ad/<int:book_id>', methods=['GET'])
def get_ad(book_id):
    """Получение одной книги по ID"""
    try:
        books = get_books_from_gas()
        book = next((b for b in books if b.get("id") == book_id), None)
        
        if book:
            return jsonify({"status": "ok", "book": book}), 200
        else:
            return jsonify({"error": "Книга не найдена"}), 404
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/delete_ad/<int:book_id>', methods=['DELETE'])
def delete_ad(book_id):
    """Удаление книги"""
    try:
        books = get_books_from_gas()
        original_count = len(books)
        books = [b for b in books if b.get("id") != book_id]
        
        if len(books) < original_count:
            if save_books_to_gas(books):
                logger.info(f"🗑️ Книга #{book_id} удалена")
                return jsonify({"status": "ok", "message": "Книга удалена"}), 200
        
        return jsonify({"error": "Книга не найдена"}), 404
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['GET'])
def search_books():
    """Поиск книг"""
    try:
        query = request.args.get('q', '').lower()
        if not query:
            return get_ads()
        
        books = get_books_from_gas()
        results = [
            b for b in books 
            if query in b.get('title', '').lower() 
            or query in b.get('author', '').lower()
        ]
        
        return jsonify({
            "status": "ok",
            "books": results,
            "total": len(results),
            "query": query
        }), 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

# ============ НАСТРОЙКА WEBHOOK ============

bot_app = None

def setup_bot():
    """Настройка бота и установка webhook"""
    global bot_app
    
    logger.info("🔧 Настройка бота...")
    
    bot_app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CommandHandler("books", books_command))
    
    webhook_url = f"{RENDER_URL}/webhook"
    webhook_url = clean_url(webhook_url)
    logger.info(f"🔗 URL вебхука: {webhook_url}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(bot_app.bot.set_webhook(webhook_url))
        logger.info(f"✅ Webhook установлен")
        
        webhook_info = loop.run_until_complete(bot_app.bot.get_webhook_info())
        logger.info(f"📡 Webhook info: {webhook_info.url}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}")
        raise
    finally:
        loop.close()
    
    logger.info("🤖 Бот готов!")

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Обработка webhook от Telegram"""
    if not bot_app:
        return jsonify({"error": "Bot not initialized"}), 500
    
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot_app.bot)
        await bot_app.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ============ ЗАПУСК ============

if __name__ == "__main__":
    try:
        setup_bot()
        port = int(os.environ.get('PORT', 10000))
        logger.info(f"🚀 Запуск на порту {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        exit(1)
