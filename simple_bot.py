import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

books = []

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def css():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def js():
    return send_from_directory('.', 'script.js')

@app.route('/health')
def health():
    return jsonify({"status": "ok", "books": len(books)})

@app.route('/save_ad', methods=['POST'])
def save_ad():
    try:
        data = request.get_json()
        logger.info(f"Получено: {data}")
        
        new_book = {
            "id": len(books) + 1,
            "title": data.get('title', 'Без названия'),
            "author": data.get('author', 'Неизвестен'),
            "price": data.get('price', 0),
            "contact": data.get('contact', ''),
            "date": __import__('datetime').datetime.now().isoformat()
        }
        
        books.append(new_book)
        return jsonify({"status": "ok", "book": new_book}), 200
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_ads', methods=['GET'])
def get_ads():
    return jsonify({"books": books, "total": len(books)})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)