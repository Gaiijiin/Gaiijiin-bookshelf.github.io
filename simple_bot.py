import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# Получение токена и URL из переменных окружения
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://telegrambot-sbae.onrender.com')

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
    exit(1)

# Глобальная переменная для приложения бота
bot_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот, который работает на Render через webhook!\n"
        "Отправь мне любое сообщение, и я его повторю."
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
        "Просто отправь любое сообщение, и я его повторю!"
    )

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "Бот работает через webhook!"}), 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Обработка webhook запросов от Telegram"""
    if not bot_app:
        return jsonify({"error": "Bot not initialized"}), 500
    
    try:
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        await bot_app.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return jsonify({"error": str(e)}), 500

def setup_bot():
    """Настройка бота и установка webhook"""
    global bot_app
    
    # Создаем приложение
    bot_app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Устанавливаем webhook
    webhook_url = f"{RENDER_URL}/webhook"
    
    # Запускаем асинхронную установку webhook
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(bot_app.bot.set_webhook(webhook_url))
        logger.info(f"✅ Webhook установлен: {webhook_url}")
    finally:
        loop.close()
    
    logger.info("🤖 Бот готов к работе через webhook!")

# Запуск приложения
if __name__ == "__main__":
    setup_bot()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
