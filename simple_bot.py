import os
import re
import logging
import asyncio
from flask import Flask, request, jsonify, send_from_directory
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

def clean_url(url: str) -> str:
    """Очищает URL от непечатных символов"""
    if not url:
        return url
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', url)
    return cleaned.strip()

# Получение переменных окружения
TOKEN = clean_url(os.environ.get('TELEGRAM_BOT_TOKEN', ''))
RENDER_URL = clean_url(os.environ.get('RENDER_EXTERNAL_URL', 'https://telegrambot-sbae.onrender.com'))

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
    exit(1)

logger.info(f"✅ Бот запускается с URL: {RENDER_URL}")

# Хранилище объявлений
ads = []

# Создаем приложение бота
bot_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет кнопку с мини-приложением"""
    # URL твоего мини-приложения
    webapp_url = f"{RENDER_URL}/static/index.html"  # Если есть статические файлы
    # Или просто: webapp_url = RENDER_URL
    
    # Создаем кнопку
    keyboard = [[InlineKeyboardButton(
        text="📚 Открыть Bookshelf", 
        web_app=WebAppInfo(url=webapp_url)
    )]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Добро пожаловать в Bookshelf!\n\n"
        "📖 Мини-приложение для продажи книг\n\n"
        "👇 Нажми на кнопку ниже, чтобы открыть",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    await update.message.reply_text(
        "📚 Bookshelf Bot\n\n"
        "Отправь /start, чтобы открыть мини-приложение"
    )

# Регистрируем обработчики
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))

# Flask маршруты
@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "Bookshelf Bot is running!"}), 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "ads_count": len(ads)}), 200

@app.route('/save_ad', methods=['POST'])
def save_ad():
    """Сохранение объявления"""
    try:
        data = request.get_json()
        logger.info(f"📝 Получено объявление: {data}")
        
        ad = {
            "id": len(ads) + 1,
            "title": data.get('title'),
            "description": data.get('description', ''),
            "price": data.get('price'),
            "contact": data.get('contact'),
            "created_at": __import__('datetime').datetime.now().isoformat()
        }
        
        ads.append(ad)
        logger.info(f"✅ Сохранено. Всего: {len(ads)}")
        
        return jsonify({"status": "ok", "message": "Объявление сохранено", "id": ad["id"]}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    """Получить все объявления"""
    return jsonify({"ads": ads}), 200

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Webhook для Telegram"""
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot_app.bot)
        await bot_app.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Ошибка webhook: {e}")
        return jsonify({"error": str(e)}), 500

def setup_webhook():
    """Установка webhook"""
    webhook_url = f"{RENDER_URL}/webhook"
    
    async def set_webhook():
        await bot_app.bot.set_webhook(webhook_url)
        info = await bot_app.bot.get_webhook_info()
        logger.info(f"✅ Webhook: {info.url}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(set_webhook())
    loop.close()

# Запуск
if __name__ == "__main__":
    setup_webhook()
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)