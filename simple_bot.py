import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# ДИАГНОСТИКА - покажет все переменные окружения
print("=" * 60)
print("ДИАГНОСТИКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
print("=" * 60)
for key in ['RENDER_EXTERNAL_URL', 'RENDER_SERVICE_NAME', 'RENDER_SERVICE_ID', 'PORT', 'TELEGRAM_BOT_TOKEN']:
    value = os.environ.get(key)
    if value and 'TOKEN' in key:
        print(f"{key}: {value[:10]}... (длина: {len(value)})")
    else:
        print(f"{key}: {value if value else 'НЕ УСТАНОВЛЕНА'}")
print("=" * 60)

# Получение токена
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
    exit(1)

# ПРАВИЛЬНОЕ получение URL Render
# Render автоматически устанавливает RENDER_EXTERNAL_URL только для некоторых типов сервисов
# Поэтому получаем URL из нескольких источников
RENDER_URL = None

# 1. Пробуем RENDER_EXTERNAL_URL (обычно доступен для веб-сервисов)
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')

# 2. Если нет, пробуем сформировать из имени сервиса
if not RENDER_URL:
    service_name = os.environ.get('RENDER_SERVICE_NAME')
    if service_name:
        RENDER_URL = f"https://{service_name}.onrender.com"
        logger.info(f"📍 Сформирован URL из RENDER_SERVICE_NAME: {RENDER_URL}")

# 3. Если всё еще нет, используем значение по умолчанию (замени на свой реальный URL)
if not RENDER_URL:
    # ВСТАВЬ СВОЙ РЕАЛЬНЫЙ URL ОТ RENDER!
    RENDER_URL = "https://telegrambot-sbae.onrender.com"  # <-- УБЕДИСЬ, ЧТО ЭТО ПРАВИЛЬНЫЙ URL
    logger.warning(f"⚠️ Используется URL по умолчанию: {RENDER_URL}")

logger.info(f"✅ Будет использован URL: {RENDER_URL}")

# Глобальная переменная для приложения бота
bot_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот Bookshelf!\n"
        "📚 Используй мини-приложение для создания объявлений о книгах.\n\n"
        "Команды:\n"
        "/start - Начать работу\n"
        "/help - Помощь"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    await update.message.reply_text(f"📝 Ты сказал: {user_message}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🤖 Доступные команды:\n"
        "/start - Начать работу\n"
        "/help - Помощь\n\n"
        "📱 Открой мини-приложение, чтобы создать объявление!"
    )

@app.route('/')
def index():
    return jsonify({
        "status": "ok", 
        "message": "Bookshelf Bot работает!",
        "webhook_url": f"{RENDER_URL}/webhook" if RENDER_URL else "not configured"
    }), 200

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "bot_configured": bool(bot_app),
        "webhook_url": f"{RENDER_URL}/webhook" if RENDER_URL else "not configured"
    }), 200

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Обработка webhook запросов от Telegram"""
    if not bot_app:
        logger.error("Бот не инициализирован")
        return jsonify({"error": "Bot not initialized"}), 500
    
    try:
        # Получаем JSON из запроса
        json_data = request.get_json(force=True)
        if not json_data:
            return jsonify({"error": "No JSON data"}), 400
            
        logger.info(f"📨 Получен webhook: {json_data.get('message', {}).get('text', 'no text')}")
        
        update = Update.de_json(json_data, bot_app.bot)
        await bot_app.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def setup_bot():
    """Настройка бота и установка webhook"""
    global bot_app
    
    logger.info("🔧 Настройка бота...")
    
    # Создаем приложение
    bot_app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Формируем URL вебхука
    webhook_url = f"{RENDER_URL}/webhook"
    logger.info(f"🔗 URL вебхука: {webhook_url}")
    
    # Устанавливаем webhook
    try:
        # Создаем новый event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Устанавливаем webhook
        loop.run_until_complete(bot_app.bot.set_webhook(webhook_url))
        logger.info(f"✅ Webhook успешно установлен: {webhook_url}")
        
        # Проверяем, что webhook установлен
        webhook_info = loop.run_until_complete(bot_app.bot.get_webhook_info())
        logger.info(f"📡 Информация о webhook: url={webhook_info.url}, pending_updates={webhook_info.pending_update_count}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при установке webhook: {e}")
        logger.error(f"Тип ошибки: {type(e).__name__}")
        raise
    finally:
        loop.close()
    
    logger.info("🤖 Бот готов к работе через webhook!")

# Запуск приложения
if __name__ == "__main__":
    try:
        setup_bot()
        
        port = int(os.environ.get('PORT', 10000))
        logger.info(f"🚀 Запуск Flask сервера на порту {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        exit(1)
