// ========== TELEGRAM ==========
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.expand();
    tg.ready();
}
const isTelegram = !!tg?.initData;

// ========== SUPABASE ==========
const SUPABASE_URL = 'https://tebovawnnybsglhznoha.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRlYm92YXdubnlic2dsaHpub2hhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUyMDY1MzcsImV4cCI6MjA5MDc4MjUzN30.aRdc6JZs0BKyDTCjGbTUZUn7X212ZATtgk8sK25E1EU';

// ========== АДМИН ==========
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

// ========== ЗВЁЗДЫ ==========
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
let ebooks = [];
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
        renderBuyBooks();
        console.log('✅ Загружено книг для продажи:', physicalBooks.length);
        return true;
    } catch (error) {
        console.error('❌ Ошибка загрузки книг для продажи:', error);
        return false;
    }
}

async function loadEbooksFromSupabase() {
    try {
        const response = await fetch(`${SUPABASE_URL}/rest/v1/ebooks?select=*`, {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
            }
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        let data = await response.json();
        
        // Сортировка: сначала по series, затем по volume (число)
        data.sort((a, b) => {
            const seriesA = a.series || '';
            const seriesB = b.series || '';
            if (seriesA !== seriesB) {
                return seriesA.localeCompare(seriesB);
            }
            const volA = a.volume ? parseInt(a.volume, 10) : Infinity;
            const volB = b.volume ? parseInt(b.volume, 10) : Infinity;
            return volA - volB;
        });
        
        ebooks = data;
        renderReadBooks();
        console.log('✅ Загружено книг для чтения:', ebooks.length);
        return true;
    } catch (error) {
        console.error('❌ Ошибка загрузки книг для чтения:', error);
        return false;
    }
}

async function saveBookToSupabase(bookData) {
    try {
        const cleanData = {
            title: bookData.title,
            author: bookData.author,
            price: parseFloat(bookData.price),
            contact: bookData.contact,
            created_at: new Date().toISOString()
        };
        
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

// ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
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
    
    if (!ebooks || ebooks.length === 0) {
        container.innerHTML = '<div class="empty">📭 Книг пока нет</div>';
        return;
    }
    
    let filtered = ebooks;
    if (currentReadGenre !== 'all') {
        filtered = ebooks.filter(b => b.genre === currentReadGenre);
    }
    
    if (!filtered.length) {
        container.innerHTML = '<div class="empty">📭 Книг пока нет</div>';
        return;
    }
    
    // Группировка по сериям
    const groups = {};
    filtered.forEach(book => {
        const key = book.series || book.id;
        if (!groups[key]) {
            groups[key] = {
                title: book.series || book.title,
                author: book.author,
                description: book.description,
                cover_url: book.cover_url,
                books: []
            };
        }
        if (book.series) {
            groups[key].books.push(book);
        } else {
            groups[key].books = [book];
        }
    });
    
    container.innerHTML = Object.values(groups).map(group => {
        if (group.books.length > 1) {
            // Серия с несколькими томами
            const volumesHtml = group.books.map(book => `
                <button class="volume-btn" onclick="readBook('${book.id}')">Том ${book.volume}</button>
            `).join('');
            return `
                <div class="book-card series-card">
                    <div class="book-cover">
                        ${group.cover_url ? `<img src="${group.cover_url}" alt="Обложка" class="cover-image">` : '<div class="cover-placeholder">📚</div>'}
                    </div>
                    <div class="book-info">
                        <div class="book-title">${escapeHtml(group.title)}</div>
                        <div class="book-author">${escapeHtml(group.author)}</div>
                        <div class="volumes-container" style="display: none;" id="volumes-${group.title.replace(/\s/g, '')}">
                            ${volumesHtml}
                        </div>
                        <button class="contact-btn" onclick="toggleVolumes('${group.title.replace(/\s/g, '')}')">📖 Выбрать том</button>
                    </div>
                </div>
            `;
        } else {
            // Одиночная книга
            const book = group.books[0];
            return `
                <div class="book-card">
                    <div class="book-cover">
                        ${book.cover_url ? `<img src="${book.cover_url}" alt="Обложка" class="cover-image">` : '<div class="cover-placeholder">📖</div>'}
                    </div>
                    <div class="book-info">
                        <div class="book-title">${escapeHtml(book.title)}</div>
                        <div class="book-author">${escapeHtml(book.author)}</div>
                        <div class="book-description">${escapeHtml(book.description || '')}</div>
                       <button class="contact-btn" onclick="readBook('${book.id}')">📖 Читать онлайн</button>
<button class="share-btn" onclick="shareBook('${book.id}', '${escapeHtml(book.title)}')">🔗 Поделиться</button>
                    </div>
                </div>
            `;
        }
    }).join('');
}

// Функция для показа/скрытия томов
window.toggleVolumes = function(seriesId) {
    const container = document.getElementById(`volumes-${seriesId}`);
    if (container) {
        container.style.display = container.style.display === 'none' ? 'flex' : 'none';
    }
};
// ========== ОТРИСОВКА КНИГ ДЛЯ ПОКУПКИ ==========
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
        const isSeller = book.contact === currentUserName;
        
        let genreEmoji = "📚";
        if (book.genre === "манга") genreEmoji = "📖";
        else if (book.genre === "ранобэ") genreEmoji = "📘";
        else if (book.genre === "комиксы") genreEmoji = "🦸";
        else if (book.genre === "классика") genreEmoji = "📜";
        else if (book.genre === "роман21") genreEmoji = "🌟";
        
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
                <button class="share-btn" onclick="shareBook('${book.id}', '${escapeHtml(book.title)}')">🔗 Поделиться</button>
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
window.readBook = async function(bookId) {
    const book = ebooks.find(b => b.id == bookId);
    
    if (!book) {
        const msg = "❌ Книга не найдена";
        if (isTelegram && tg?.showPopup) {
            tg.showPopup({ title: "Ошибка", message: msg, buttons: [{ type: "ok" }] });
        } else {
            alert(msg);
        }
        return;
    }
    
    if (book.epub_url) {
        // Открываем ссылку на файл напрямую
        if (isTelegram && tg?.openLink) {
            tg.openLink(book.epub_url);
        } else if (isTelegram && tg?.openTelegramLink) {
            tg.openTelegramLink(book.epub_url);
        } else {
            window.open(book.epub_url, '_blank');
        }
    } else {
        const msg = `📖 Книга "${book.title}" временно недоступна.`;
        if (isTelegram && tg?.showPopup) {
            tg.showPopup({ title: "📖 Чтение", message: msg, buttons: [{ type: "ok" }] });
        } else {
            alert(msg);
        }
    }
};
window.contactSeller = function(username, bookTitle) {
    const cleanUsername = String(username || '').replace('@', '').trim();
    
    if (!cleanUsername) {
        const msg = "❌ Контакт продавца не указан";
        if (window.Telegram?.WebApp?.showPopup) {
            window.Telegram.WebApp.showPopup({ title: "Ошибка", message: msg, buttons: [{ type: "ok" }] });
        } else {
            alert(msg);
        }
        return;
    }
    
    const tgLink = `https://t.me/${cleanUsername}`;
    const warning = `\n\nПлощадка ТОЛЬКО сводит покупателя и продавца.\nМы НЕ храним деньги, НЕ отвечаем за сделки.\n\nПерейти к продавцу?`;
    
    const openLink = () => {
        if (window.Telegram?.WebApp?.openTelegramLink) {
            window.Telegram.WebApp.openTelegramLink(tgLink);
        } else {
            window.open(tgLink, '_blank');
        }
    };
    
    if (window.Telegram?.WebApp?.showPopup) {
        window.Telegram.WebApp.showPopup({
            title: "⚠️ ВНИМАНИЕ",
            message: warning,
            buttons: [
                { id: "cancel", type: "cancel", text: "❌ Отмена" },
                { id: "go", type: "default", text: "✅ Перейти" }
            ]
        }, (buttonId) => {
            if (buttonId === "go") openLink();
        });
    } else if (confirm(warning)) {
        openLink();
    }
};

window.deleteBook = async function(bookId) {
    const book = physicalBooks.find(b => b.id === bookId);
    if (!book) {
        alert("Книга не найдена");
        return;
    }
    
    const currentUser = getCurrentUser();
    const isSeller = book.contact === currentUser;
    
    if (!isSeller && !isAdminMode) {
        alert("❌ Вы можете удалять только свои объявления");
        return;
    }
    
    if (confirm(`🗑️ Удалить товар "${book.title}"?`)) {
        const success = await deleteBookFromSupabase(bookId);
        if (success) {
            physicalBooks = physicalBooks.filter(b => b.id !== bookId);
            renderBuyBooks();
            alert("✅ Товар удалён");
        } else {
            alert("❌ Не удалось удалить");
        }
    }
};
// ========== ПОДЕЛИТЬСЯ КНИГОЙ ==========
window.shareBook = function(bookId, bookTitle) {
    const botUsername = "bybookshelfbot";
    const link = `https://t.me/${botUsername}?start=read_${bookId}`;
    if (isTelegram && tg?.showPopup) {
        tg.showPopup({
            title: "📤 Поделиться книгой",
            message: `Поделитесь ссылкой на книгу "${bookTitle}":\n\n${link}`,
            buttons: [{ type: "ok" }]
        });
    } else {
        prompt("Скопируйте ссылку для отправки:", link);
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
    alert("Спасибо за отзыв!");
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
    alert("Отзыв обновлён");
};

window.deleteReviewConfirm = function(bookId, reviewIndex) {
    if (confirm('Удалить этот отзыв?')) {
        reviews[bookId].splice(reviewIndex, 1);
        if (reviews[bookId].length === 0) delete reviews[bookId];
        saveReviewsLocally();
        renderBuyBooks();
        alert("Отзыв удалён");
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
        alert("Отзыв удалён");
    }
};

// ========== АДМИН-РЕЖИМ ==========
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
                tg.showPopup({ title: "🔓 Админ-режим", message: "Активирован", buttons: [{ type: "ok" }] });
            } else {
                alert("🔓 Админ-режим активирован!");
            }
        } else {
            alert("❌ У вас нет прав администратора");
        }
        adminClickCount = 0;
    }
});

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
            alert("✅ Книга успешно опубликована!");
        } else {
            throw new Error(result.error || 'Ошибка сохранения');
        }
    } catch (error) {
        console.error('❌ Ошибка:', error);
        alert(`❌ Ошибка: ${error.message}`);
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
            msg.innerHTML = '🔍 Ничего не найдено';
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

// ========== ПОИСК ВО ВКЛАДКЕ ЧИТАТЬ ==========
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
            msg.innerHTML = '🔍 Ничего не найдено';
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

// ========== ЗАПУСК ==========
loadReviewsLocally();
loadBooksFromSupabase();
loadEbooksFromSupabase();
