import os
import logging
import requests
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("❌ Нет токена!")
    exit(1)

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://telegrambot-sbae.onrender.com')
logger.info(f"✅ Бот запущен: {RENDER_URL}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📚 Открыть Bookshelf", web_app=WebAppInfo(url=RENDER_URL))]]
    await update.message.reply_text(
        "👋 Добро пожаловать в Bookshelf!\n\n👇 Нажми на кнопку",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(f"{RENDER_URL}/get_ads", timeout=10)
        books = response.json().get('books', [])
        
        if not books:
            await update.message.reply_text("📚 Книг пока нет")
            return
        
        msg = "📚 Книги:\n\n"
        for b in books[-10:]:
            msg += f"📖 {b['title']} - {b['price']} руб.\n"
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Ошибка загрузки книг")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("books", books_command))
    
    logger.info("🚀 Бот запущен и работает!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
