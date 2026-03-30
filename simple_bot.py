import os
import logging
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8611738780:AAElmgb8Qcqk9pRkQBu8Lcl9QxVeun6zFSo"
MINI_APP_URL = "https://bybookshelf.netlify.app"
PORT = int(os.environ.get("PORT", 5000))

logging.basicConfig(level=logging.INFO)

flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "🤖 Bot is running!"

@flask_app.route('/health')
def health():
    return "OK", 200

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if args and args[0].startswith("book_"):
        await update.message.reply_text("📖 Функция отправки книг появится позже.")
        return

    keyboard = [[InlineKeyboardButton("📖 Открыть книжный магазин", web_app={"url": MINI_APP_URL})]]
    await update.message.reply_text(
        f"📚 Добро пожаловать, {user.first_name}!\n\n👇 Нажми на кнопку, чтобы открыть магазин.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Запускаем бота в основном потоке (с event loop)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    logging.info("🤖 Бот запущен и работает!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
