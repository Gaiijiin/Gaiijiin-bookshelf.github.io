import requests
import json

# Константа с вашим URL веб-приложения Google Apps Script
GAS_URL = 'https://script.google.com/macros/s/AKfycbzvg08q_MxKeivLR8BqCMt5feZpKPJcbaw6Y2_jDbaAM0SmViYB2t4SBtZTkK_xkweH/exec'

# --- ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ КНИГ (GET) ---
def get_books_from_gas():
    """Получает список книг из Google Apps Script."""
    try:
        response = requests.get(GAS_URL)
        if response.status_code == 200:
            # Парсим JSON-ответ от вашего скрипта
            books_data = response.json()
            # Ваш скрипт, судя по doGet, возвращает объект с полем 'books'
            return books_data.get('books', [])
        else:
            print(f"Ошибка при получении книг: {response.status_code}")
            return []
    except Exception as e:
        print(f"Исключение при запросе к GAS: {e}")
        return []

# --- ФУНКЦИЯ ДЛЯ СОХРАНЕНИЯ КНИГ (POST) ---
def save_books_to_gas(books_list):
    """Сохраняет список книг через Google Apps Script."""
    payload = {
        "books": books_list  # Отправляем список книг, как ожидает ваш doPost
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(GAS_URL, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("Книги успешно сохранены в репозиторий!")
                return True
            else:
                print(f"Ошибка от GAS: {result.get('error')}")
                return False
        else:
            print(f"Ошибка HTTP при сохранении: {response.status_code}")
            return False
    except Exception as e:
        print(f"Исключение при сохранении книг: {e}")
        return False

# ===== ПРИМЕР ИСПОЛЬЗОВАНИЯ В ВАШЕМ ОСНОВНОМ КОДЕ =====
# Допустим, это вызывается в обработчике Flask для '/save_ad'
# @app.route('/save_ad', methods=['POST'])
# def save_ad_endpoint():
#     data = request.get_json()
#     # ... ваша логика ...
#     
#     # Получаем текущий список книг
#     current_books = get_books_from_gas()
#     
#     # Добавляем новую книгу
#     new_book = {"title": data['title'], "author": data['author']}
#     current_books.append(new_book)
#     
#     # Сохраняем обновленный список
#     if save_books_to_gas(current_books):
#         return jsonify({"status": "ok", "message": "Книга добавлена!"}), 200
#     else:
#         return jsonify({"status": "error", "message": "Ошибка сохранения"}), 500
