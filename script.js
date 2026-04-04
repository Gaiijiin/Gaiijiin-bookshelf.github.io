// ========== TELEGRAM ==========
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.expand();
    tg.ready();
}
const isTelegram = !!tg?.initData;

// ========== SUPABASE (ПРЯМОЕ ПОДКЛЮЧЕНИЕ) ==========
const SUPABASE_URL = 'https://tebovawnnybsglhznoha.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRlYm92YXdubnlic2dsaHpub2hhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUyMDY1MzcsImV4cCI6MjA5MDc4MjUzN30.aRdc6JZs0BKyDTCjGbTUZUn7X212ZATtgk8sK25E1EU';

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
const fullText = 'BOOKSHELF';
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

// ========== ГЛОБАЛЬНЫЕ ДАННЫЕ ==========
let physicalBooks = [];
let nextBookId = 1;
let reviews = {};

// ========== ФУНКЦИИ РАБОТЫ С SUPABASE ==========
async function loadBooksFromSupabase() {
    try {
        const response = await fetch(`${SUPABASE_URL}/rest/v1/books?select=*&order=created_at.desc`, {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
            }
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        physicalBooks = data;
        nextBookId = Math.max(...physicalBooks.map(b => b.id), 0) + 1;
        renderBuyBooks();
        console.log('✅ Загружено книг:', physicalBooks.length);
        return true;
    } catch (error) {
        console.error('❌ Ошибка загрузки книг:', error);
        return false;
    }
}

async function saveBookToSupabase(bookData) {
    try {
        // Отправляем ТОЛЬКО поля, которые есть в таблице books
        const cleanData = {
            title: bookData.title,
            author: bookData.author,
            price: parseFloat(bookData.price),
            contact: bookData.contact,
            created_at: new Date().toISOString()
        };
        
        // Если есть genre – добавляем
        if (bookData.genre) cleanData.genre = bookData.genre;
        
        console.log('📤 Отправка в Supabase:', cleanData);
        
        const response = await fetch(`${SUPABASE_URL}/rest/v1/books`, {
            method: 'POST',
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(cleanData)
        });
        
        const text = await response.text();
        console.log('📡 Статус:', response.status, 'Ответ:', text);
        
        if (response.ok) {
            return { success: true, book: bookData };
        } else {
            return { success: false, error: text };
        }
    } catch (error) {
        console.error('❌ Ошибка отправки:', error);
        return { success: false, error: error.message };
    }
}

async function deleteBookFromSupabase(bookId) {
    try {
        const response = await fetch(`${SUPABASE_URL}/rest/v1/books?id=eq.${bookId}`, {
            method: 'DELETE',
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
            }
        });
        return response.ok;
    } catch (error) {
        console.error('❌ Ошибка удаления:', error);
        return false;
    }
}

// ========== ДАННЫЕ ДЛЯ ЧТЕНИЯ (ЛОКАЛЬНЫЕ) ==========
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

let currentUser = null;
let currentReadGenre = "all";
let currentBuyGenre = "all";

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

function getToday() {
    return new Date().toISOString().split('T')[0];
}

function formatDate(dateStr) {
    if (!dateStr) return 'недавно';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return 'недавно';
    return `${date.getDate()}.${date.getMonth()+1}.${date.getFullYear()}`;
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

function renderStars(rating) {
    let stars = '';
    for (let i = 0; i < Math.floor(rating); i++) stars += '⭐';
    for (let i = stars.length; i < 5; i++) stars += '☆';
    return stars;
}

function getAvgRating(bookId) {
    if (!reviews[bookId] || reviews[bookId].length === 0) return null;
    const sum = reviews[bookId].reduce((a, r) => a + r.rating, 0);
    return (sum / reviews[bookId].length).toFixed(1);
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
            <div class="book-title">${escapeHtml(book.title)}</div>
            <div class="book-author">${escapeHtml(book.author)}</div>
            <div style="opacity:0.7">${escapeHtml(book.description)}</div>
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
        // Проверяем, является ли текущий пользователь продавцом
        const isSeller = book.contact === currentUserName;
        
        let genreEmoji = "📚";
        if (book.genre === "манга") genreEmoji = "📖";
        else if (book.genre === "ранобэ") genreEmoji = "📘";
        else if (book.genre === "комиксы") genreEmoji = "🦸";
        else if (book.genre === "классика") genreEmoji = "📜";
        else if (book.genre === "роман21") genreEmoji = "🌟";
        
        // Безопасное экранирование для onclick
        const safeTitle = escapeHtml(book.title).replace(/'/g, "\\'");
        const sellerContact = book.contact ? book.contact.replace('@', '') : '';
        
        return `
            <div class="book-card">
                <div class="book-title">${genreEmoji} ${escapeHtml(book.title)}</div>
                <div class="book-author">${escapeHtml(book.author)}</div>
                <div class="book-date">📅 Добавлено: ${formatDate(book.created_at || book.date)}</div>
                <div class="rating-display">${avg ? renderStars(parseFloat(avg)) + ' <span class="rating-value">' + avg + '</span>' : '⭐ Нет отзывов'}</div>
                <div>Состояние: ${book.condition || 'хорошее'}</div>
                <div class="book-price">💰 ${book.price} ₽</div>
                <div>Продавец: ${escapeHtml(book.contact) || 'Не указан'}</div>
                <button class="contact-btn" onclick="contactSeller('${sellerContact}', '${safeTitle}')">📩 Купить / Связаться</button>
                <button class="review-btn" onclick="openReviewModal('${book.id}', '${safeTitle}')">✍️ Оставить отзыв</button>
                ${(isSeller || isAdminMode) ? `<button class="admin-delete-btn" onclick="deleteBook('${book.id}')">🗑️ Удалить товар</button>` : ''}
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
                    ${isAuthor ? `<span class="review-edit" onclick="openEditReviewModal('${bookId}', ${idx})">✏️</span>` : ''}
                    ${(isAuthor || showAdminDelete) ? `<span class="review-delete" onclick="deleteReviewConfirm('${bookId}', ${idx})">🗑️</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
}
// ========== ФУНКЦИИ ДЛЯ КНИГ ==========

/**
 * Чтение книги – отправляет EPUB-файл через Telegram бота
 * @param {string|number} bookId - ID книги
 */
window.readBook = async function(bookId) {
    // 1. Ищем книгу в физических объявлениях (Supabase)
    let book = physicalBooks.find(b => b.id == bookId);
    
    // 2. Если не нашли – ищем в локальной базе ebooks (вкладка "Читать")
    if (!book) {
        for (let genre in ebooks) {
            book = ebooks[genre].find(b => b.id == bookId);
            if (book) break;
        }
    }
    
    // 3. Если книга не найдена – показываем ошибку
    if (!book) {
        const msg = "❌ Книга не найдена";
        if (isTelegram && tg?.showPopup) {
            tg.showPopup({ title: "Ошибка", message: msg, buttons: [{ type: "ok" }] });
        } else {
            alert(msg);
        }
        return;
    }
    
    // 4. Проверяем, есть ли ссылка на EPUB-файл
    if (book.epub_url) {
        // Ссылка на бота (укажи username своего бота, например "my_bookshelf_bot")
        const BOT_USERNAME = "bybookshelfbot";
        const tgLink = `https://t.me/${BOT_USERNAME}?start=read_${book.id}`;
        
        const msg = `📖 Книга "${book.title}" будет отправлена в бота.\n\nНажмите "Открыть", чтобы перейти в бота и получить файл.`;
        
        if (isTelegram && tg?.showPopup) {
            tg.showPopup({
                title: "📖 Чтение",
                message: msg,
                buttons: [
                    { id: "cancel", type: "cancel", text: "❌ Отмена" },
                    { id: "open", type: "default", text: "✅ Открыть бота" }
                ]
            }, (buttonId) => {
                if (buttonId === "open") {
                    tg.openTelegramLink(tgLink);
                }
            });
        } else {
            if (confirm(msg.replace(/\n/g, ' '))) {
                window.open(tgLink, '_blank');
            }
        }
    } else {
        // 5. Если EPUB-файла нет – сообщаем, что книга временно недоступна
        const msg = `📖 Книга "${book.title}" временно недоступна для скачивания.\nПожалуйста, попробуйте позже.`;
        if (isTelegram && tg?.showPopup) {
            tg.showPopup({ title: "📖 Чтение", message: msg, buttons: [{ type: "ok" }] });
        } else {
            alert(msg);
        }
    }
};
// ========== СВЯЗЬ С ПРОДАВЦОМ ==========
window.contactSeller = function(username, bookTitle) {
    // Очищаем username от @ и пробелов
    const cleanUsername = String(username || '').replace('@', '').trim();
    
    if (!cleanUsername) {
        const errorMsg = "❌ Контакт продавца не указан.\n\nПожалуйста, сообщите продавцу, чтобы он добавил свой Telegram в объявлении.";
        if (isTelegram && tg?.showPopup) {
            tg.showPopup({ title: "Ошибка", message: errorMsg, buttons: [{ type: "ok" }] });
        } else {
            alert(errorMsg);
        }
        return;
    }
    
    const message = `⚠️ ВНИМАНИЕ! ЗОНА ОТВЕТСТВЕННОСТИ ПОКУПАТЕЛЯ ⚠️\n\n` +
        `Вы собираетесь связаться с продавцом книги "${bookTitle}".\n\n` +
        `📌 Площадка ТОЛЬКО сводит покупателя и продавца.\n` +
        `📌 Мы НЕ проверяем книги, НЕ храним деньги, НЕ отвечаем за сделки.\n\n` +
        `🔥 Обязательно:\n` +
        `• Попросите 3-4 фото книги\n` +
        `• Уточните состояние\n` +
        `• Не переводите деньги без проверки\n` +
        `• Встречайтесь лично\n\n` +
        `Перейти в профиль продавца?`;
    
    const tgLink = `https://t.me/${cleanUsername}`;
    
    // Функция для открытия ссылки (надёжный способ)
    const openLink = function(url) {
        // Способ 1: через Telegram WebApp (если доступен)
        if (isTelegram && tg?.openTelegramLink) {
            tg.openTelegramLink(url);
        } 
        // Способ 2: создаём временную ссылку и эмулируем клик (работает в WebApp)
        else if (window.Telegram?.WebApp) {
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        // Способ 3: обычный window.open
        else if (window.open) {
            window.open(url, '_blank');
        }
        // Способ 4: последний шанс – показываем ссылку
        else {
            alert(`Перейдите по ссылке: ${url}`);
        }
    };
    
    // В Telegram WebApp используем popup с подтверждением
    if (isTelegram && tg?.showPopup) {
        tg.showPopup({
            title: "📢 Внимание",
            message: message,
            buttons: [
                { id: "back", type: "cancel", text: "❌ Назад" },
                { id: "go", type: "default", text: "✅ Перейти" }
            ]
        }, (buttonId) => {
            if (buttonId === "go") {
                openLink(tgLink);
            }
        });
    } 
    // В обычном браузере используем confirm и открытие ссылки
    else {
        if (confirm(message)) {
            openLink(tgLink);
        }
    }
};

// ========== УДАЛЕНИЕ КНИГИ ==========
window.deleteBook = async function(bookId) {
    const book = physicalBooks.find(b => b.id === bookId);
    if (!book) {
        const errorMsg = "❌ Книга не найдена";
        if (isTelegram && tg?.showPopup) {
            tg.showPopup({ title: "Ошибка", message: errorMsg, buttons: [{ type: "ok" }] });
        } else {
            alert(errorMsg);
        }
        return;
    }
    
    const currentUser = getCurrentUser();
    const isSeller = book.contact === currentUser;
    
    if (!isSeller && !isAdminMode) {
        const errorMsg = "❌ Вы можете удалять только свои объявления";
        if (isTelegram && tg?.showPopup) {
            tg.showPopup({ title: "Ошибка", message: errorMsg, buttons: [{ type: "ok" }] });
        } else {
            alert(errorMsg);
        }
        return;
    }
    
    const confirmMsg = `🗑️ Удалить товар "${book.title}"?\n\nЭто действие нельзя отменить.`;
    
    const confirmed = isTelegram && tg?.showPopup 
        ? await new Promise((resolve) => {
            tg.showPopup({
                title: "Подтверждение",
                message: confirmMsg,
                buttons: [
                    { id: "cancel", type: "cancel", text: "❌ Отмена" },
                    { id: "ok", type: "ok", text: "✅ Удалить" }
                ]
            }, (buttonId) => {
                resolve(buttonId === "ok");
            });
        })
        : confirm(confirmMsg);
    
    if (confirmed) {
        const success = await deleteBookFromSupabase(bookId);
        if (success) {
            physicalBooks = physicalBooks.filter(b => b.id !== bookId);
            renderBuyBooks();
            const successMsg = "✅ Товар успешно удалён из базы данных";
            if (isTelegram && tg?.showPopup) {
                tg.showPopup({ title: "🗑️ Удалено", message: successMsg, buttons: [{ type: "ok" }] });
            } else {
                alert(successMsg);
            }
        } else {
            const errorMsg = "❌ Не удалось удалить книгу. Попробуйте позже.";
            if (isTelegram && tg?.showPopup) {
                tg.showPopup({ title: "Ошибка", message: errorMsg, buttons: [{ type: "ok" }] });
            } else {
                alert(errorMsg);
            }
        }
    }
};
// ========== ОТЗЫВЫ ==========
function saveReviewsLocally() {
    localStorage.setItem('bookshelf_reviews', JSON.stringify(reviews));
}

function loadReviewsLocally() {
    const savedReviews = localStorage.getItem('bookshelf_reviews');
    if (savedReviews) reviews = JSON.parse(savedReviews);
    else reviews = {};
}

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
    const bookId = document.getElementById('modalBookId').value;
    const rating = parseInt(document.getElementById('reviewRating').value);
    const text = document.getElementById('reviewText').value.trim();
    
    if (!text) {
        alert('Напишите текст отзыва');
        return;
    }
    
    const userName = getCurrentUser();
    
    if (!reviews[bookId]) reviews[bookId] = [];
    reviews[bookId].unshift({ author: userName, rating: rating, text: text, date: getToday() });
    saveReviewsLocally();
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
    const bookId = document.getElementById('editBookId').value;
    const reviewIndex = parseInt(document.getElementById('editReviewIndex').value);
    const rating = parseInt(document.getElementById('editReviewRating').value);
    const text = document.getElementById('editReviewText').value.trim();
    
    if (!text) {
        alert('Напишите текст отзыва');
        return;
    }
    
    reviews[bookId][reviewIndex].rating = rating;
    reviews[bookId][reviewIndex].text = text;
    saveReviewsLocally();
    renderBuyBooks();
    closeEditReviewModal();
    
    if (isTelegram && tg?.showPopup) tg.showPopup({ title: "✅ Обновлено!", message: "Отзыв изменён", buttons: [{ type: "ok" }] });
    else alert("Отзыв обновлён");
};

window.deleteReviewConfirm = function(bookId, reviewIndex) {
    if (confirm('Удалить этот отзыв?')) {
        reviews[bookId].splice(reviewIndex, 1);
        if (reviews[bookId].length === 0) delete reviews[bookId];
        saveReviewsLocally();
        renderBuyBooks();
        if (isTelegram && tg?.showPopup) tg.showPopup({ title: "🗑️ Удалено", message: "Отзыв удалён", buttons: [{ type: "ok" }] });
        else alert("Отзыв удалён");
    }
};

window.deleteReview = function() {
    const bookId = document.getElementById('editBookId').value;
    const reviewIndex = parseInt(document.getElementById('editReviewIndex').value);
    if (confirm('Удалить этот отзыв?')) {
        reviews[bookId].splice(reviewIndex, 1);
        if (reviews[bookId].length === 0) delete reviews[bookId];
        saveReviewsLocally();
        renderBuyBooks();
        closeEditReviewModal();
        if (isTelegram && tg?.showPopup) tg.showPopup({ title: "🗑️ Удалено", message: "Отзыв удалён", buttons: [{ type: "ok" }] });
        else alert("Отзыв удалён");
    }
};

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

// ========== ФОРМА ПРОДАЖИ (СОХРАНЕНИЕ В SUPABASE) ==========
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
    
    // Отправляем ТОЛЬКО поля, которые есть в таблице books
    const bookData = {
        title: document.getElementById('title').value.trim(),
        author: document.getElementById('author').value.trim(),
        genre: genreMap[document.getElementById('genre').value] || 'другое',
        price: parseFloat(document.getElementById('price').value),
        contact: document.getElementById('contact').value.trim(),
        created_at: new Date().toISOString()
    };
    
    if (!bookData.title || !bookData.author || isNaN(bookData.price) || !bookData.contact) {
        alert('❌ Заполните все поля');
        return;
    }
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '⏳ Публикация...';
    submitBtn.disabled = true;
    
    try {
        const result = await saveBookToSupabase(bookData);
        
        if (result.success) {
            await loadBooksFromSupabase();
            renderBuyBooks();
            document.getElementById('sell-form').reset();
            const msg = "✅ Книга успешно опубликована!";
            if (isTelegram && tg?.showPopup) {
                tg.showPopup({ title: "Готово!", message: msg, buttons: [{ type: "ok" }] });
            } else {
                alert(msg);
            }
        } else {
            throw new Error(result.error || 'Ошибка сохранения');
        }
    } catch (error) {
        console.error('❌ Ошибка публикации:', error);
        alert(`❌ Ошибка публикации: ${error.message}\nПопробуйте позже.`);
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
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
        
        if (tabId === 'buy') {
            loadBooksFromSupabase();
        }
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
        filterReadBooks(); 
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
        filterReadBooks();
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

// ========== ДРОПДАУН МЕНЮ ==========
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

// ========== ПОИСК ВО ВКЛАДКЕ "ЧИТАТЬ" ==========
const readSearchInput = document.getElementById('readSearchInput');
const readSearchClearBtn = document.getElementById('readSearchClearBtn');

function filterReadBooks() {
    const searchTerm = readSearchInput.value.toLowerCase().trim();
    const bookCards = document.querySelectorAll('#read-books-list .book-card');
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

    const noResultsMsg = document.getElementById('read-no-results');
    if (!hasVisible && searchTerm !== '') {
        if (!noResultsMsg) {
            const msg = document.createElement('div');
            msg.id = 'read-no-results';
            msg.className = 'empty';
            msg.innerHTML = '🔍 Ничего не найдено. Попробуйте другое название.';
            document.getElementById('read-books-list').appendChild(msg);
        }
    } else if (noResultsMsg) {
        noResultsMsg.remove();
    }
}

if (readSearchClearBtn) {
    readSearchClearBtn.addEventListener('click', () => {
        readSearchInput.value = '';
        filterReadBooks();
        readSearchClearBtn.style.display = 'none';
    });
}

if (readSearchInput) {
    readSearchInput.addEventListener('input', () => {
        filterReadBooks();
        readSearchClearBtn.style.display = readSearchInput.value ? 'block' : 'none';
    });
}

// ========== ЗАПУСК ==========
loadReviewsLocally();
loadBooksFromSupabase();
renderReadBooks();
filterReadBooks();
