import os
import logging
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8611738780:AAElmgb8Qcqk9pRkQBu8Lcl9QxVeun6zFSo"
MINI_APP_URL = "https://Gaiijiin.github.io/Gaiijiin-bookshelf.github.io"
PORT = int(os.environ.get("PORT", 5000))

logging.basicConfig(level=logging.INFO)

# ========== КНИГИ (ID → ФАЙЛ) ==========
BOOKS = {
    1: {"file": "berserk_1.epub", "title": "Берсерк. Том 1", "author": "Кэнтаро Миура"},
    2: {"file": "onepiece_1.epub", "title": "Ван-Пис. Том 1", "author": "Эйитиро Ода"},
    10: {"file": "Anna-Karenina.epub", "title": "Анна Каренина", "author": "Лев Толстой"},
}

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

    # Если есть аргумент book_XXX — отправляем книгу
    if args and args[0].startswith("book_"):
        try:
            book_id = int(args[0].split("_")[1])
            
            if book_id in BOOKS:
                book = BOOKS[book_id]
                file_path = os.path.join("books", book["file"])
                
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        await update.message.reply_document(
                            document=f,
                            filename=book["file"],
                            caption=f"📖 *{book['title']}*\n✍️ {book['author']}\n\nПриятного чтения! 📚",
                            parse_mode="Markdown"
                        )
                    logging.info(f"✅ Книга {book_id} отправлена пользователю {user.id}")
                else:
                    await update.message.reply_text("❌ Файл книги временно недоступен. Попробуйте позже.")
            else:
                await update.message.reply_text("❌ Книга не найдена. Проверьте ID.")
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            await update.message.reply_text("❌ Ошибка при отправке книги.")
        return

    # Обычная команда /start — показываем кнопку Mini App
    keyboard = [[InlineKeyboardButton("📖 Открыть книжный магазин", web_app={"url": MINI_APP_URL})]]
    await update.message.reply_text(
        f"📚 Добро пожаловать в КНИЖНЫЙ ШКАФ, {user.first_name}!\n\n👇 Нажми на кнопку, чтобы открыть магазин.",
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
