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
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============ ФУНКЦИЯ ОЧИСТКИ URL ============
def clean_url(url: str) -> str:
    """Удаляет непечатные символы из URL"""
    if not url:
        return url
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', url)
    return cleaned.strip()

# ============ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ============
TOKEN = clean_url(os.environ.get('TELEGRAM_BOT_TOKEN', ''))
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
    exit(1)

RENDER_URL = clean_url(os.environ.get('RENDER_EXTERNAL_URL', ''))
if not RENDER_URL:
    RENDER_URL = "https://telegrambot-sbae.onrender.com"

logger.info(f"✅ Бот запущен: {RENDER_URL}")

# ============ KEEP-ALIVE (сервер не засыпает) ============
def keep_alive():
    """Пинг сервера каждые 4 минуты"""
    while True:
        time.sleep(240)
        try:
            requests.get(RENDER_URL, timeout=10)
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
    """Получение книг из Google Apps Script"""
    try:
        response = requests.get(GAS_URL, timeout=15)
        if response.status_code == 200:
            data = response.json()
            books = data.get('books', [])
            logger.info(f"✅ Загружено {len(books)} книг")
            return books
        logger.warning(f"⚠️ GAS вернул статус {response.status_code}")
        return []
    except requests.exceptions.Timeout:
        logger.error("❌ Таймаут при загрузке книг")
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return []

def save_books(books):
    """Сохранение книг в Google Apps Script"""
    try:
        response = requests.post(GAS_URL, json={"books": books}, timeout=15)
        logger.info(f"📡 GAS ответ: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP ошибка: {response.status_code}")
            return False
        
        data = response.json()
        
        # Проверяем успешность сохранения
        if data.get('success') is True:
            logger.info(f"✅ Сохранено {len(books)} книг")
            return True
        if 'books' in data:
            logger.info(f"✅ Сохранено {len(books)} книг")
            return True
        
        logger.error(f"❌ Неизвестный ответ: {data}")
        return False
        
    except requests.exceptions.Timeout:
        logger.error("❌ Таймаут при сохранении")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        return False

def add_book(title, author, price, contact):
    """Добавление новой книги"""
    try:
        books = get_books()
        
        new_book = {
            "id": len(books) + 1,
            "title": title,
            "author": author,
            "price": int(price),
            "contact": contact,
            "date": __import__('datetime').datetime.now().isoformat()
        }
        
        books.append(new_book)
        
        if save_books(books):
            logger.info(f"✅ Книга добавлена: {title}")
            return True, new_book
        return False, None
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления: {e}")
        return False, None

# ============ КОМАНДЫ БОТА ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка кнопки с мини-приложением"""
    try:
        keyboard = [[InlineKeyboardButton("📚 Открыть Bookshelf", web_app=WebAppInfo(url=RENDER_URL))]]
        books_count = len(get_books())
        
        await update.message.reply_text(
            f"👋 Добро пожаловать в Bookshelf!\n\n"
            f"📚 В базе {books_count} книг\n\n"
            f"👇 Нажми на кнопку, чтобы открыть приложение",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"✅ Команда /start от {update.effective_user.username}")
    except Exception as e:
        logger.error(f"❌ Ошибка в start: {e}")

async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список книг"""
    try:
        books = get_books()
        if not books:
            await update.message.reply_text("📚 Книг пока нет")
            return
        
        message = "📚 Последние книги:\n\n"
        for book in books[-10:]:
            message += f"📖 {book.get('title', '?')} - {book.get('price', '?')} руб.\n"
        message += f"\nВсего книг: {len(books)}"
        
        await update.message.reply_text(message)
        logger.info(f"✅ Команда /books от {update.effective_user.username}")
    except Exception as e:
        logger.error(f"❌ Ошибка в books: {e}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Эхо для теста"""
    try:
        await update.message.reply_text(f"Я получил: {update.message.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка в echo: {e}")

# ============ FLASK МАРШРУТЫ ============
@app.route('/')
def index():
    """Главная страница"""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки index: {e}")
        return "Ошибка загрузки страницы", 500

@app.route('/style.css')
def css():
    try:
        return send_from_directory('.', 'style.css')
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки CSS: {e}")
        return "", 404

@app.route('/script.js')
def js():
    try:
        return send_from_directory('.', 'script.js')
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки JS: {e}")
        return "", 404

@app.route('/health')
def health():
    """Проверка здоровья сервиса"""
    return jsonify({
        "status": "healthy",
        "books_count": len(get_books()),
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

@app.route('/save_ad', methods=['POST', 'OPTIONS'])
def save_ad():
    """Сохранение объявления"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Нет данных"}), 400
        
        logger.info(f"📥 Получено объявление: {data}")
        
        # Валидация
        title = data.get('title')
        if not title or not title.strip():
            return jsonify({"error": "Название книги обязательно"}), 400
        
        author = data.get('author', 'Неизвестен')
        price = data.get('price', 0)
        contact = data.get('contact', '')
        
        if not contact:
            return jsonify({"error": "Контакт для связи обязателен"}), 400
        
        # Сохраняем
        success, book = add_book(title, author, price, contact)
        
        if success:
            return jsonify({
                "status": "ok",
                "message": "Книга успешно добавлена",
                "book": book
            }), 200
        else:
            return jsonify({"error": "Ошибка сохранения в базу данных"}), 500
            
    except Exception as e:
        logger.error(f"❌ Ошибка save_ad: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    """Получение всех объявлений"""
    try:
        books = get_books()
        return jsonify({
            "status": "ok",
            "books": books,
            "total": len(books)
        }), 200
    except Exception as e:
        logger.error(f"❌ Ошибка get_ads: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка webhook от Telegram"""
    global bot_app
    if not bot_app:
        return jsonify({"error": "Bot not ready"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        
        # Создаем event loop для обработки
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            update = Update.de_json(data, bot_app.bot)
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
    """Настройка бота и установка webhook"""
    global bot_app
    logger.info("🔧 Настройка бота...")
    
    try:
        # Создаем приложение
        bot_app = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("books", books_command))
        bot_app.add_handler(CommandHandler("help", books_command))  # help показывает книги
        bot_app.add_handler(CommandHandler("echo", echo))
        
        # Инициализируем в event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(bot_app.initialize())
        loop.run_until_complete(bot_app.bot.set_webhook(f"{RENDER_URL}/webhook"))
        
        loop.close()
        
        logger.info(f"✅ Webhook установлен: {RENDER_URL}/webhook")
        logger.info("🤖 Бот готов к работе!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки бота: {e}")
        raise

# ============ ЗАПУСК ============
if __name__ == "__main__":
    try:
        setup_bot()
        port = int(os.environ.get('PORT', 10000))
        logger.info(f"🚀 Запуск Flask сервера на порту {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        exit(1)
