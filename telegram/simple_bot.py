import os
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import threading

# ========== НАСТРОЙКИ ==========
TOKEN = "8611738780:AAElmgb8Qcqk9pRkQBu8Lcl9QxVeun6zFSo"
MINI_APP_URL = "https://bybookshelf.netlify.app"
PORT = int(os.environ.get("PORT", 5000))

# ========== ЛОГИ ==========
logging.basicConfig(level=logging.INFO)

# ========== КНИГИ (ID → ФАЙЛ) ==========
BOOKS = {
    1: {"file": "berserk_1.epub", "title": "Берсерк. Том 1", "author": "Кэнтаро Миура"},
    2: {"file": "onepiece_1.epub", "title": "Ван-Пис. Том 1", "author": "Эйитиро Ода"},
    3: {"file": "magic_battle.epub", "title": "Магическая битва", "author": "Гэгэ Акутами"},
    4: {"file": "spiderman.fb2", "title": "Человек-паук", "author": "Marvel"},
    8: {"file": "crime_punishment.epub", "title": "Преступление и наказание", "author": "Фёдор Достоевский"},
    9: {"file": "1984.epub", "title": "1984", "author": "Джордж Оруэлл"},
    10: {"file": "anna_karenina.epub", "title": "Анна Каренина", "author": "Лев Толстой"},
    11: {"file": "goldfinch.epub", "title": "Щегол", "author": "Донна Тартт"},
    12: {"file": "little_life.epub", "title": "Маленькая жизнь", "author": "Ханья Янагихара"},
}

# ========== FLASK ДЛЯ HEALTH CHECK ==========
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "🤖 Bot is running!"

@flask_app.route('/health')
def health():
    return "OK", 200

# ========== ТЕЛЕГРАМ БОТ ==========
telegram_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    
    # Если есть аргумент book_ID — отправляем книгу
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
                    await update.message.reply_text("❌ Файл книги временно недоступен.")
                    logging.warning(f"❌ Файл не найден: {file_path}")
            else:
                await update.message.reply_text("❌ Книга не найдена.")
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            await update.message.reply_text("❌ Ошибка при отправке книги.")
        return
    
    # Обычный /start — показываем кнопку Mini App
    keyboard = [[InlineKeyboardButton("📖 Открыть книжный магазин", web_app={"url": MINI_APP_URL})]]
    await update.message.reply_text(
        f"📚 Добро пожаловать в КНИЖНЫЙ ШКАФ, {user.first_name}!\n\n"
        "📖 Здесь вы можете:\n"
        "• Читать книги онлайн\n"
        "• Покупать книги у других\n"
        "• Продавать свои книги\n\n"
        "👇 Нажми на кнопку, чтобы открыть магазин",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def run_bot():
    """Запуск Telegram бота"""
    global telegram_app
    telegram_app = Application.builder().token(TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    
    logging.info("🤖 Бот запущен и работает!")
    telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask для health check (чтобы Render не убил бота)
    flask_app.run(host="0.0.0.0", port=PORT)