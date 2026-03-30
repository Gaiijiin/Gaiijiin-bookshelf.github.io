// ========== TELEGRAM ==========
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.expand();
    tg.ready();
}
const isTelegram = !!tg?.initData;

// ========== АДМИН ПО TELEGRAM ID ==========
let isAdminMode = false;
const ADMIN_IDS = [798388659];

function isAdmin() {
    if (isTelegram && tg?.initDataUnsafe?.user) {
        return ADMIN_IDS.includes(tg.initDataUnsafe.user.id);
    }
    return false;
}

// ========== ПЕЧАТНАЯ МАШИНКА ==========
const titleElement = document.getElementById('typing-title');
const fullText = '📚 КНИЖНЫЙ ШКАФ';
let idx = 0;
function typeWriter() {
    if (idx < fullText.length) {
        titleElement.textContent += fullText.charAt(idx);
        idx++;
        setTimeout(typeWriter, 80);
    }
}
typeWriter();

// ========== ЗВЁЗДЫ НА ФОНЕ ==========
for (let i = 0; i < 60; i++) {
    const star = document.createElement('div');
    star.classList.add('star-bg');
    star.style.width = (Math.random() * 2.5 + 1) + 'px';
    star.style.height = star.style.width;
    star.style.left = Math.random() * 100 + '%';
    star.style.top = Math.random() * 100 + '%';
    star.style.animationDuration = (Math.random() * 4 + 2) + 's';
    star.style.animationDelay = (Math.random() * 8) + 's';
    document.body.appendChild(star);
}

// ========== GOOGLE APPS SCRIPT API ==========
const GAS_URL = 'https://script.google.com/macros/s/AKfycbzvg08q_MxKeivLR8BqCMt5feZpKPJcbaw6Y2_jDbaAM0SmViYB2t4SBtZTkK_xkweH/exec';

// Загрузка объявлений
async function loadBooksFromGitHub() {
    try {
        const response = await fetch(GAS_URL);
        const json = await response.json();
        physicalBooks = json.books || [];
        nextBookId = Math.max(...physicalBooks.map(b => b.id), 0) + 1;
        renderBuyBooks();
        console.log('✅ Загружено книг:', physicalBooks.length);
    } catch (error) {
        console.error('❌ Ошибка загрузки:', error);
        // Если не работает, загружаем локально
        loadData();
    }
}

// Сохранение объявлений
async function saveBooksToGitHub() {
    try {
        const response = await fetch(GAS_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ books: physicalBooks })
        });
        const result = await response.json();
        return result.success === true;
    } catch (error) {
        console.error('❌ Ошибка сохранения:', error);
        return false;
    }
}

// Загрузка объявлений из GitHub (все пользователи)
async function loadBooksFromGitHub() {
    try {
        const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${FILE_PATH}`);
        if (!response.ok) {
            console.log('Файл books.json не найден, создаём новый');
            physicalBooks = [];
            nextBookId = 1;
            renderBuyBooks();
            return;
        }
        const data = await response.json();
        const content = atob(data.content);
        const json = JSON.parse(content);
        physicalBooks = json.books || [];
        nextBookId = Math.max(...physicalBooks.map(b => b.id), 0) + 1;
        renderBuyBooks();
        console.log('✅ Загружено книг из GitHub:', physicalBooks.length);
    } catch (error) {
        console.error('❌ Ошибка загрузки:', error);
        loadData(); // fallback на локальное
    }
}

// Сохранение объявлений в GitHub (любой пользователь может сохранять)
async function saveBooksToGitHub() {
    try {
        // Получаем SHA текущего файла
        let sha = null;
        try {
            const shaRes = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${FILE_PATH}`, {
                headers: { 'Authorization': `token ${GITHUB_TOKEN}` }
            });
            if (shaRes.ok) {
                const shaData = await shaRes.json();
                sha = shaData.sha;
            }
        } catch(e) {
            console.log('Файл ещё не существует');
        }
        
        const content = btoa(unescape(encodeURIComponent(JSON.stringify({ books: physicalBooks }, null, 2))));
        const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${FILE_PATH}`, {
            method: 'PUT',
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: `Update books (${new Date().toLocaleString()})`, 
                content: content, 
                sha: sha 
            })
        });
        
        if (response.ok) {
            console.log('✅ Сохранено в GitHub');
            return true;
        } else {
            const error = await response.json();
            console.error('❌ Ошибка сохранения:', error);
            return false;
        }
    } catch (error) {
        console.error('❌ Ошибка сети:', error);
        return false;
    }
}

// ========== ДАННЫЕ ==========
let reviews = {};
let physicalBooks = [];
let currentReadGenre = "all";
let currentBuyGenre = "all";
let nextBookId = 1;
let currentUser = null;

// ========== КНИГИ ДЛЯ ЧТЕНИЯ ==========
const ebooks = {
    manga: [
        { id: 1, title: "Берсерк. Том 1", author: "Кэнтаро Миура", description: "Тёмное фэнтези" },
        { id: 2, title: "Ван-Пис. Том 1", author: "Эйитиро Ода", description: "Приключения" }
    ],
    ranobe: [
        { id: 3, title: "Магическая битва", author: "Гэгэ Акутами", description: "Битвы магов" }
    ],
    comics: [
        { id: 4, title: "Человек-паук", author: "Marvel", description: "Паучий мир" }
    ],
    classic: [
        { id: 8, title: "Преступление и наказание", author: "Фёдор Достоевский", description: "Роман о морали и искуплении" },
        { id: 9, title: "1984", author: "Джордж Оруэлл", description: "Антиутопия" },
        { id: 10, title: "Анна Каренина", author: "Лев Толстой", description: "Трагическая история любви" }
    ],
    modern: [
        { id: 11, title: "Щегол", author: "Донна Тартт", description: "Пулитцеровская премия" },
        { id: 12, title: "Маленькая жизнь", author: "Ханья Янагихара", description: "Современная классика" }
    ],
    fantasy: [
        { id: 20, title: "Властелин колец", author: "Дж. Р. Р. Толкин", description: "Эпическое фэнтези" },
        { id: 21, title: "Игра престолов", author: "Джордж Мартин", description: "Политическое фэнтези" }
    ],
    thriller: [
        { id: 22, title: "Молчание ягнят", author: "Томас Харрис", description: "Психологический триллер" },
        { id: 23, title: "Девушка с татуировкой дракона", author: "Стиг Ларссон", description: "Детективный триллер" }
    ],
    dark: [
        { id: 24, title: "Мизери", author: "Стивен Кинг", description: "Психологический хоррор" },
        { id: 25, title: "Американский психопат", author: "Брет Истон Эллис", description: "Тёмная сатира" }
    ],
    detective: [
        { id: 26, title: "Убийство в Восточном экспрессе", author: "Агата Кристи", description: "Классический детектив" },
        { id: 27, title: "Шерлок Холмс", author: "Артур Конан Дойл", description: "Знаменитый сыщик" }
    ],
    horror: [
        { id: 28, title: "Оно", author: "Стивен Кинг", description: "Классика ужасов" },
        { id: 29, title: "Зов Ктулху", author: "Говард Лавкрафт", description: "Мистический ужас" }
    ],
    romance: [
        { id: 30, title: "Гордость и предубеждение", author: "Джейн Остин", description: "Классический роман" },
        { id: 31, title: "Дневник памяти", author: "Николас Спаркс", description: "Современная романтика" }
    ],
    "sci-fi": [
        { id: 32, title: "Дюна", author: "Фрэнк Герберт", description: "Эпическая научная фантастика" },
        { id: 33, title: "Автостопом по галактике", author: "Дуглас Адамс", description: "Юмористическая фантастика" }
    ],
    adventure: [
        { id: 34, title: "Остров сокровищ", author: "Роберт Стивенсон", description: "Пиратские приключения" },
        { id: 35, title: "Вокруг света за 80 дней", author: "Жюль Верн", description: "Приключенческий роман" }
    ]
};

function getCurrentUser() {
    if (currentUser) return currentUser;
    if (isTelegram && tg?.initDataUnsafe?.user) {
        const user = tg.initDataUnsafe.user;
        currentUser = user.username ? `@${user.username}` : (user.first_name || "Гость");
    } else {
        currentUser = localStorage.getItem('bookshelf_user') || "Гость";
    }
    return currentUser;
}

// ========== АКТИВАЦИЯ АДМИН-РЕЖИМА ==========
let adminClickCount = 0;
let adminClickTimer = null;
document.querySelector('.glow-title')?.addEventListener('click', () => {
    adminClickCount++;
    if (adminClickTimer) clearTimeout(adminClickTimer);
    adminClickTimer = setTimeout(() => { adminClickCount = 0; }, 1000);
    
    if (adminClickCount === 3) {
        if (isAdmin()) {
            isAdminMode = true;
            renderBuyBooks();
            if (isTelegram && tg?.showPopup) {
                tg.showPopup({ title: "🔓 Админ-режим", message: "Активирован. Вы видите кнопки удаления.", buttons: [{ type: "ok" }] });
            } else {
                alert("🔓 Админ-режим активирован!");
            }
        } else {
            if (isTelegram && tg?.showPopup) {
                tg.showPopup({ title: "❌ Доступ запрещён", message: "У вас нет прав администратора", buttons: [{ type: "ok" }] });
            } else {
                alert("❌ У вас нет прав администратора. Откройте приложение в Telegram.");
            }
        }
        adminClickCount = 0;
    }
});

// ========== ЗАГРУЗКА / СОХРАНЕНИЕ (ЛОКАЛЬНОЕ) ==========
function loadData() {
    const savedReviews = localStorage.getItem('bookshelf_reviews');
    if (savedReviews) reviews = JSON.parse(savedReviews);
    else reviews = {};
    
    const savedBooks = localStorage.getItem('bookshelf_listings');
    if (savedBooks) {
        const parsed = JSON.parse(savedBooks);
        physicalBooks = parsed.books;
        nextBookId = parsed.nextId;
    } else {
        physicalBooks = [
            { id: 1, title: "Берсерк. Том 1", author: "Кэнтаро Миура", genre: "манга", condition: "отличное", price: 500, seller: "book_lover", sellerName: "@book_lover", date: "2026-03-20" },
            { id: 2, title: "Ван-Пис. Том 1", author: "Эйитиро Ода", genre: "манга", condition: "хорошее", price: 400, seller: "manga_fan", sellerName: "@manga_fan", date: "2026-03-21" },
            { id: 5, title: "Преступление и наказание", author: "Фёдор Достоевский", genre: "классика", condition: "отличное", price: 350, seller: "classic_reader", sellerName: "@classic_reader", date: "2026-03-22" },
            { id: 6, title: "1984", author: "Джордж Оруэлл", genre: "классика", condition: "хорошее", price: 300, seller: "bookworm", sellerName: "@bookworm", date: "2026-03-22" },
            { id: 7, title: "Щегол", author: "Донна Тартт", genre: "роман21", condition: "отличное", price: 550, seller: "modern_reader", sellerName: "@modern_reader", date: "2026-03-23" }
        ];
        nextBookId = 8;
    }
}

function saveData() {
    localStorage.setItem('bookshelf_reviews', JSON.stringify(reviews));
    localStorage.setItem('bookshelf_listings', JSON.stringify({ books: physicalBooks, nextId: nextBookId }));
}

// ========== ВСПОМОГАТЕЛЬНЫЕ ==========
function getAvgRating(bookId) {
    if (!reviews[bookId] || reviews[bookId].length === 0) return null;
    const sum = reviews[bookId].reduce((a, r) => a + r.rating, 0);
    return (sum / reviews[bookId].length).toFixed(1);
}

function renderStars(rating) {
    let stars = '';
    for (let i = 0; i < Math.floor(rating); i++) stars += '⭐';
    for (let i = stars.length; i < 5; i++) stars += '☆';
    return stars;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function getToday() {
    return new Date().toISOString().split('T')[0];
}

function formatDate(dateStr) {
    if (!dateStr) return 'недавно';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return 'недавно';
    return `${date.getDate()}.${date.getMonth()+1}.${date.getFullYear()}`;
}

// ========== ОТРИСОВКА КНИГ ДЛЯ ЧТЕНИЯ ==========
function renderReadBooks() {
    const container = document.getElementById('read-books-list');
    let books = [];
    
    if (currentReadGenre === 'all') {
        for (let genre in ebooks) {
            books = books.concat(ebooks[genre]);
        }
    } else {
        books = ebooks[currentReadGenre] || [];
    }
    
    if (!books.length) {
        container.innerHTML = '<div class="empty">📭 Книг пока нет</div>';
        return;
    }
    
    container.innerHTML = books.map(book => `
        <div class="book-card">
            <div class="book-title">${book.title}</div>
            <div class="book-author">${book.author}</div>
            <div style="opacity:0.7">${book.description}</div>
            <button class="contact-btn" onclick="readBook(${book.id})">📖 Читать онлайн</button>
        </div>
    `).join('');
}

// ========== ОТРИСОВКА ОБЪЯВЛЕНИЙ ДЛЯ ПОКУПКИ ==========
function renderBuyBooks() {
    const container = document.getElementById('buy-books-list');
    let filtered = physicalBooks;
    
    if (currentBuyGenre !== 'all') {
        filtered = physicalBooks.filter(b => b.genre === currentBuyGenre);
    }
    
    if (!filtered.length) {
        container.innerHTML = '<div class="empty">📭 Книг пока нет</div>';
        return;
    }
    
    const currentUserName = getCurrentUser();
    
    container.innerHTML = filtered.map(book => {
        const avg = getAvgRating(book.id);
        const bookReviews = reviews[book.id] || [];
        const isSeller = book.sellerName === currentUserName;
        
        let genreEmoji = "📚";
        if (book.genre === "манга") genreEmoji = "📖";
        else if (book.genre === "ранобэ") genreEmoji = "📘";
        else if (book.genre === "комиксы") genreEmoji = "🦸";
        else if (book.genre === "классика") genreEmoji = "📜";
        else if (book.genre === "роман21") genreEmoji = "🌟";
        
        return `
            <div class="book-card">
                <div class="book-title">${genreEmoji} ${escapeHtml(book.title)}</div>
                <div class="book-author">${escapeHtml(book.author)}</div>
                <div class="book-date">📅 Добавлено: ${formatDate(book.date)}</div>
                <div class="rating-display">${avg ? renderStars(parseFloat(avg)) + ' <span class="rating-value">' + avg + '</span>' : '⭐ Нет отзывов'}</div>
                <div>Состояние: ${book.condition}</div>
                <div class="book-price">💰 ${book.price} ₽</div>
                <div>Продавец: ${book.sellerName}</div>
                <button class="contact-btn" onclick="contactSeller('${book.seller}', '${escapeHtml(book.title).replace(/'/g, "\\'")}')">📩 Купить / Связаться</button>
                <button class="review-btn" onclick="openReviewModal(${book.id}, '${escapeHtml(book.title).replace(/'/g, "\\'")}')">✍️ Оставить отзыв</button>
                ${(isSeller || isAdminMode) ? `<button class="admin-delete-btn" onclick="deleteBook(${book.id})">🗑️ Удалить товар</button>` : ''}
                <div class="reviews-section">
                    <div class="reviews-title">📝 Отзывы (${bookReviews.length})</div>
                    ${renderReviews(book.id)}
                </div>
            </div>
        `;
    }).join('');
}

function renderReviews(bookId) {
    if (!reviews[bookId] || reviews[bookId].length === 0) return '<div class="no-reviews">Пока нет отзывов</div>';
    
    const currentUser = getCurrentUser();
    
    return reviews[bookId].map((rev, idx) => {
        const isAuthor = rev.author === currentUser;
        const showAdminDelete = isAdminMode;
        
        return `
            <div class="review-item">
                <div class="review-header">
                    <span class="review-author">${escapeHtml(rev.author)}</span>
                    <span class="review-stars">${renderStars(rev.rating)}</span>
                    <span class="review-date">${rev.date}</span>
                </div>
                <div class="review-text">${escapeHtml(rev.text)}</div>
                <div class="review-actions">
                    ${isAuthor ? `<span class="review-edit" onclick="openEditReviewModal(${bookId}, ${idx})">✏️</span>` : ''}
                    ${(isAuthor || showAdminDelete) ? `<span class="review-delete" onclick="deleteReviewConfirm(${bookId}, ${idx})">🗑️</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// ========== ГЛОБАЛЬНЫЕ ФУНКЦИИ ==========
window.readBook = function(bookId) {
    const msg = "Функция чтения появится в следующей версии";
    if (isTelegram && tg?.showPopup) tg.showPopup({ title: "📖 Чтение", message: msg, buttons: [{ type: "ok" }] });
    else alert(msg);
};

window.contactSeller = function(username, bookTitle) {
    const message = `⚠️ ЗОНА ОТВЕТСТВЕННОСТИ ПОКУПАТЕЛЯ ⚠️\n\nВы собираетесь связаться с продавцом книги "${bookTitle}".\n\n📌 Площадка ТОЛЬКО сводит покупателя и продавца.\n📌 Мы НЕ проверяем книги, НЕ храним деньги, НЕ отвечаем за сделки.\n\n🔥 Обязательно:\n• Попросите 3-4 фото книги\n• Уточните состояние\n• Не переводите деньги без проверки\n• Встречайтесь лично\n\nПерейти в Telegram?`;
    
    if (isTelegram && tg?.showPopup) {
        tg.showPopup({
            title: "📢 Внимание",
            message: message,
            buttons: [
                { id: "back", type: "cancel", text: "❌ Назад" },
                { id: "go", type: "default", text: "✅ Перейти" }
            ]
        }, (buttonId) => {
            if (buttonId === "go") tg.openTelegramLink(`https://t.me/${username.replace('@', '')}`);
        });
    } else {
        if (confirm(message)) window.open(`https://t.me/${username.replace('@', '')}`, '_blank');
    }
};

// ========== УДАЛЕНИЕ ТОВАРА ==========
window.deleteBook = function(bookId) {
    const book = physicalBooks.find(b => b.id === bookId);
    if (!book) return;
    
    const currentUser = getCurrentUser();
    const isSeller = book.sellerName === currentUser;
    
    if (!isSeller && !isAdminMode) {
        alert("Вы можете удалять только свои объявления");
        return;
    }
    
    if (confirm(`Удалить товар "${book.title}"?`)) {
        physicalBooks = physicalBooks.filter(b => b.id !== bookId);
        saveData();
        renderBuyBooks();
        if (isTelegram && tg?.showPopup) tg.showPopup({ title: "🗑️ Удалено", message: "Товар удалён", buttons: [{ type: "ok" }] });
        else alert("Товар удалён");
    }
};

// ========== ОТЗЫВЫ ==========
window.openReviewModal = function(bookId, bookTitle) {
    const modal = document.getElementById('reviewModal');
    document.getElementById('modalBookTitle').textContent = bookTitle;
    document.getElementById('modalBookId').value = bookId;
    document.getElementById('reviewText').value = '';
    document.getElementById('reviewRating').value = '5';
    modal.style.display = 'flex';
};

window.closeReviewModal = function() {
    document.getElementById('reviewModal').style.display = 'none';
};

window.submitReview = function() {
    const bookId = parseInt(document.getElementById('modalBookId').value);
    const rating = parseInt(document.getElementById('reviewRating').value);
    const text = document.getElementById('reviewText').value.trim();
    
    if (!text) {
        alert('Напишите текст отзыва');
        return;
    }
    
    const userName = getCurrentUser();
    
    if (!reviews[bookId]) reviews[bookId] = [];
    reviews[bookId].unshift({ author: userName, rating: rating, text: text, date: getToday() });
    saveData();
    renderBuyBooks();
    closeReviewModal();
    
    if (isTelegram && tg?.showPopup) tg.showPopup({ title: "✅ Спасибо!", message: "Отзыв опубликован", buttons: [{ type: "ok" }] });
    else alert("Спасибо за отзыв!");
};

window.openEditReviewModal = function(bookId, reviewIndex) {
    const review = reviews[bookId][reviewIndex];
    const modal = document.getElementById('editReviewModal');
    document.getElementById('editBookId').value = bookId;
    document.getElementById('editReviewIndex').value = reviewIndex;
    
    const ratingSelect = document.getElementById('editReviewRating');
    ratingSelect.innerHTML = '';
    for (let i = 5; i >= 1; i--) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = '★'.repeat(i) + '☆'.repeat(5-i) + ` (${i})`;
        if (review.rating === i) option.selected = true;
        ratingSelect.appendChild(option);
    }
    
    document.getElementById('editReviewText').value = review.text;
    modal.style.display = 'flex';
};

window.closeEditReviewModal = function() {
    document.getElementById('editReviewModal').style.display = 'none';
};

window.updateReview = function() {
    const bookId = parseInt(document.getElementById('editBookId').value);
    const reviewIndex = parseInt(document.getElementById('editReviewIndex').value);
    const rating = parseInt(document.getElementById('editReviewRating').value);
    const text = document.getElementById('editReviewText').value.trim();
    
    if (!text) {
        alert('Напишите текст отзыва');
        return;
    }
    
    reviews[bookId][reviewIndex].rating = rating;
    reviews[bookId][reviewIndex].text = text;
    saveData();
    renderBuyBooks();
    closeEditReviewModal();
    
    if (isTelegram && tg?.showPopup) tg.showPopup({ title: "✅ Обновлено!", message: "Отзыв изменён", buttons: [{ type: "ok" }] });
    else alert("Отзыв обновлён");
};

window.deleteReviewConfirm = function(bookId, reviewIndex) {
    if (confirm('Удалить этот отзыв?')) {
        reviews[bookId].splice(reviewIndex, 1);
        if (reviews[bookId].length === 0) delete reviews[bookId];
        saveData();
        renderBuyBooks();
        if (isTelegram && tg?.showPopup) tg.showPopup({ title: "🗑️ Удалено", message: "Отзыв удалён", buttons: [{ type: "ok" }] });
        else alert("Отзыв удалён");
    }
};

window.deleteReview = function() {
    const bookId = parseInt(document.getElementById('editBookId').value);
    const reviewIndex = parseInt(document.getElementById('editReviewIndex').value);
    if (confirm('Удалить этот отзыв?')) {
        reviews[bookId].splice(reviewIndex, 1);
        if (reviews[bookId].length === 0) delete reviews[bookId];
        saveData();
        renderBuyBooks();
        closeEditReviewModal();
        if (isTelegram && tg?.showPopup) tg.showPopup({ title: "🗑️ Удалено", message: "Отзыв удалён", buttons: [{ type: "ok" }] });
        else alert("Отзыв удалён");
    }
};

// ========== ФОРМА ПРОДАЖИ ==========
document.getElementById('sell-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const genreMap = {
        'Манга': 'манга',
        'Ранобэ': 'ранобэ',
        'Комиксы': 'комиксы',
        'Классика': 'классика',
        'Роман 21 века': 'роман21',
        'Другое': 'другое'
    };
    
    const newBook = {
        id: nextBookId++,
        title: document.getElementById('title').value,
        author: document.getElementById('author').value,
        genre: genreMap[document.getElementById('genre').value] || 'другое',
        condition: document.getElementById('condition').value,
        price: parseInt(document.getElementById('price').value),
        seller: document.getElementById('contact').value.replace('@', ''),
        sellerName: document.getElementById('contact').value,
        date: getToday()
    };
    
    if (!newBook.title || !newBook.author || !newBook.price || !newBook.seller) {
        alert('Заполните все поля');
        return;
    }
    
    physicalBooks.push(newBook);
    
    const success = await saveBooksToGitHub();
    if (success) {
        renderBuyBooks();
        document.getElementById('sell-form').reset();
        const msg = "✅ Объявление опубликовано! Книга появится у всех пользователей.";
        if (isTelegram && tg?.showPopup) tg.showPopup({ title: "Готово!", message: msg, buttons: [{ type: "ok" }] });
        else alert(msg);
    } else {
        alert('❌ Ошибка сохранения. Попробуйте позже.');
        physicalBooks.pop(); // откатываем добавление
        nextBookId--;
    }
});

// ========== НАВИГАЦИЯ ПО ТАБАМ ==========
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tabId = btn.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
    });
});

// ========== ЖАНРЫ ДЛЯ ЧТЕНИЯ ==========
const readAllBtn = document.getElementById('readAllBtn');
if (readAllBtn) {
    readAllBtn.addEventListener('click', () => {
        document.querySelectorAll('#read .filters-group button').forEach(b => b.classList.remove('active'));
        readAllBtn.classList.add('active');
        currentReadGenre = 'all';
        renderReadBooks();
    });
}

document.querySelectorAll('#readDropdownContent button').forEach(btn => {
    btn.addEventListener('click', () => {
        const genre = btn.dataset.genre;
        currentReadGenre = genre;
        
        document.querySelectorAll('#read .filters-group button').forEach(b => b.classList.remove('active'));
        document.getElementById('readDropdownBtn').classList.add('active');
        
        const genreNames = {
            'manga': '📖 Манга',
            'ranobe': '📘 Ранобэ',
            'comics': '🦸 Комиксы',
            'classic': '📜 Классика',
            'modern': '🌟 Романы 21 века',
            'fantasy': '✨ Фэнтези',
            'thriller': '🔪 Триллер',
            'dark': '🌑 Дарк',
            'detective': '🕵️ Детектив',
            'horror': '👻 Ужасы',
            'romance': '💕 Романтика',
            'sci-fi': '🚀 Научная фантастика',
            'adventure': '🏔️ Приключения'
        };
        document.getElementById('readDropdownBtn').innerHTML = (genreNames[genre] || '📖 Жанры') + ' ▼';
        
        renderReadBooks();
        document.getElementById('readDropdownContent').style.display = 'none';
    });
});

// ========== ЖАНРЫ ДЛЯ ПОКУПКИ ==========
const buyAllBtn = document.getElementById('buyAllBtn');
if (buyAllBtn) {
    buyAllBtn.addEventListener('click', () => {
        document.querySelectorAll('#buy .filters-group button').forEach(b => b.classList.remove('active'));
        buyAllBtn.classList.add('active');
        currentBuyGenre = 'all';
        renderBuyBooks();
    });
}

document.querySelectorAll('#buyDropdownContent button').forEach(btn => {
    btn.addEventListener('click', () => {
        const genre = btn.dataset.buyGenre;
        currentBuyGenre = genre;
        
        document.querySelectorAll('#buy .filters-group button').forEach(b => b.classList.remove('active'));
        document.getElementById('buyDropdownBtn').classList.add('active');
        
        const genreNames = {
            'манга': '📖 Манга',
            'ранобэ': '📘 Ранобэ',
            'комиксы': '🦸 Комиксы',
            'классика': '📜 Классика',
            'роман21': '🌟 Романы 21 века',
            'фэнтези': '✨ Фэнтези',
            'триллер': '🔪 Триллер',
            'дарк': '🌑 Дарк',
            'детектив': '🕵️ Детектив',
            'ужасы': '👻 Ужасы',
            'романтика': '💕 Романтика',
            'sci-fi': '🚀 Научная фантастика',
            'приключения': '🏔️ Приключения'
        };
        document.getElementById('buyDropdownBtn').innerHTML = (genreNames[genre] || '📖 Жанры') + ' ▼';
        
        renderBuyBooks();
        document.getElementById('buyDropdownContent').style.display = 'none';
    });
});

// ========== УНИВЕРСАЛЬНОЕ МЕНЮ ==========
function setupDropdown(btnId, contentId) {
    const btn = document.getElementById(btnId);
    const content = document.getElementById(contentId);
    if (!btn || !content) return;

    function closeMenu(e) {
        if (!btn.contains(e.target) && !content.contains(e.target)) {
            content.style.display = 'none';
            document.removeEventListener('click', closeMenu);
        }
    }

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = content.style.display === 'block';
        document.querySelectorAll('.dropdown-content').forEach(d => d.style.display = 'none');
        if (!isOpen) {
            content.style.display = 'block';
            setTimeout(() => document.addEventListener('click', closeMenu), 0);
        } else {
            content.style.display = 'none';
        }
    });
}

setupDropdown('readDropdownBtn', 'readDropdownContent');
setupDropdown('buyDropdownBtn', 'buyDropdownContent');

// ========== ЗВЁЗДЫ ПРИ НАВЕДЕНИИ ==========
const titleH1 = document.querySelector('.glow-title');
function createFlyingStar(x, y) {
    const star = document.createElement('div');
    star.innerHTML = ['★', '☆', '✦', '✧'][Math.floor(Math.random() * 4)];
    star.style.position = 'fixed';
    star.style.left = x + 'px';
    star.style.top = y + 'px';
    star.style.fontSize = (Math.random() * 15 + 10) + 'px';
    star.style.color = '#fff9c4';
    star.style.textShadow = '0 0 8px #ffd966';
    star.style.pointerEvents = 'none';
    star.style.zIndex = '9999';
    star.style.transition = 'all 2s ease-out';
    document.body.appendChild(star);
    setTimeout(() => {
        star.style.transform = `translate(${(Math.random() - 0.5) * 200}px, -100px)`;
        star.style.opacity = '0';
    }, 10);
    setTimeout(() => star.remove(), 2000);
}
titleH1?.addEventListener('mouseenter', (e) => {
    for (let i = 0; i < 15; i++) {
        setTimeout(() => createFlyingStar(e.clientX + (Math.random() - 0.5) * 80, e.clientY + 40), i * 50);
    }
});

// ========== ПОИСК ==========
const searchInput = document.getElementById('searchInput');
const searchClearBtn = document.getElementById('searchClearBtn');

function filterBooksBySearch() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const bookCards = document.querySelectorAll('#buy-books-list .book-card');
    
    let hasVisible = false;
    bookCards.forEach(card => {
        const title = card.querySelector('.book-title')?.textContent.toLowerCase() || '';
        if (searchTerm === '' || title.includes(searchTerm)) {
            card.style.display = '';
            hasVisible = true;
        } else {
            card.style.display = 'none';
        }
    });
    
    const noResultsMsg = document.getElementById('no-search-results');
    if (!hasVisible && searchTerm !== '') {
        if (!noResultsMsg) {
            const msg = document.createElement('div');
            msg.id = 'no-search-results';
            msg.className = 'empty';
            msg.innerHTML = '🔍 Ничего не найдено. Попробуйте другое название.';
            document.getElementById('buy-books-list').appendChild(msg);
        }
    } else if (noResultsMsg) {
        noResultsMsg.remove();
    }
}

if (searchClearBtn) {
    searchClearBtn.addEventListener('click', () => {
        searchInput.value = '';
        filterBooksBySearch();
        searchClearBtn.style.display = 'none';
    });
}

if (searchInput) {
    searchInput.addEventListener('input', () => {
        filterBooksBySearch();
        searchClearBtn.style.display = searchInput.value ? 'block' : 'none';
    });
}

// ========== ЗАПУСК ==========
loadBooksFromGitHub(); // Загружаем из GitHub
renderReadBooks();
