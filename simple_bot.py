import os
import re
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

def clean_url(url: str) -> str:
    """Очищает URL от непечатных символов и лишних пробелов."""
    if not url:
        return url
    # Удаляем все непечатные символы (включая символы \u200b, \ufeff и т.д.)
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', url)
    # Убираем пробелы и табуляции в начале и конце
    cleaned = cleaned.strip()
    return cleaned

# ДИАГНОСТИКА - покажет все переменные окружения
print("=" * 60)
print("ДИАГНОСТИКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
print("=" * 60)
for key in ['RENDER_EXTERNAL_URL', 'RENDER_SERVICE_NAME', 'RENDER_SERVICE_ID', 'PORT', 'TELEGRAM_BOT_TOKEN']:
    raw_value = os.environ.get(key)
    if raw_value:
        # Показываем длину и "чистое" значение для URL
        if 'URL' in key:
            cleaned_value = clean_url(raw_value)
            print(f"{key}: (сырая длина {len(raw_value)}) -> (чистая длина {len(cleaned_value)})")
            if len(raw_value) != len(cleaned_value):
                print(f"  ⚠️ ВНИМАНИЕ: Найдены и удалены непечатные символы!")
            print(f"  Чистый URL: {cleaned_value}")
        elif 'TOKEN' in key:
            print(f"{key}: {raw_value[:10]}... (длина: {len(raw_value)})")
        else:
            print(f"{key}: {raw_value}")
    else:
        print(f"{key}: НЕ УСТАНОВЛЕНА")
print("=" * 60)

# Получение и ОЧИСТКА токена
TOKEN_raw = os.environ.get('TELEGRAM_BOT_TOKEN')
TOKEN = clean_url(TOKEN_raw) if TOKEN_raw else None

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
    exit(1)

# Получение и ОЧИСТКА URL
RENDER_URL_raw = os.environ.get('RENDER_EXTERNAL_URL')
RENDER_URL = clean_url(RENDER_URL_raw) if RENDER_URL_raw else None

# Если нет RENDER_EXTERNAL_URL, пробуем сформировать из имени сервиса
if not RENDER_URL:
    service_name_raw = os.environ.get('RENDER_SERVICE_NAME')
    if service_name_raw:
        service_name = clean_url(service_name_raw)
        RENDER_URL = f"https://{service_name}.onrender.com"
        logger.info(f"📍 Сформирован URL из RENDER_SERVICE_NAME: {RENDER_URL}")

# Если всё еще нет, используем значение по умолчанию
if not RENDER_URL:
    RENDER_URL = "https://telegrambot-sbae.onrender.com"
    logger.warning(f"⚠️ Используется URL по умолчанию: {RENDER_URL}")

# Финальная проверка и очистка URL
RENDER_URL = clean_url(RENDER_URL)
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
        "webhook_url": f"{RENDER_URL}/webhook"
    }), 200

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "bot_configured": bool(bot_app),
        "webhook_url": f"{RENDER_URL}/webhook"
    }), 200

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Обработка webhook запросов от Telegram"""
    if not bot_app:
        logger.error("Бот не инициализирован")
        return jsonify({"error": "Bot not initialized"}), 500
    
    try:
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
    # Очищаем URL еще раз на всякий случай
    webhook_url = clean_url(webhook_url)
    logger.info(f"🔗 URL вебхука (очищенный): {webhook_url}")
    
    # Устанавливаем webhook с помощью нового event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Пытаемся установить webhook
        loop.run_until_complete(bot_app.bot.set_webhook(webhook_url))
        logger.info(f"✅ Webhook успешно установлен: {webhook_url}")
        
        # Проверяем, что webhook установлен
        webhook_info = loop.run_until_complete(bot_app.bot.get_webhook_info())
        logger.info(f"📡 Информация о webhook: url={webhook_info.url}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при установке webhook: {e}")
        logger.error(f"Тип ошибки: {type(e).__name__}")
        logger.error(f"Проблемный URL: {webhook_url}")
        logger.error(f"Длина URL: {len(webhook_url)}")
        # Показываем ASCII-коды символов в URL для диагностики
        logger.error(f"ASCII коды: {[ord(c) for c in webhook_url]}")
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
        # Запускаем Flask сервер
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        exit(1)
