// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();

let cart = JSON.parse(localStorage.getItem('cart')) || [];
let menuItems = [];
let scheduledTime = null;

// Загрузка меню
async function loadMenu() {
    try {
        const response = await fetch('/api/menu');
        menuItems = await response.json();
        displayMenu(menuItems);
        updateCartCount();
    } catch (error) {
        console.error('Ошибка загрузки меню:', error);
        // Fallback данные
        menuItems = getSampleMenu();
        displayMenu(menuItems);
    }
}

function getSampleMenu() {
    return [
        {id: 1, name: "Капучино", description: "Классический капучино с молоком", price: 180, category: "coffee"},
        {id: 2, name: "Латте", description: "Нежный латте с молочной пенкой", price: 190, category: "coffee"},
        {id: 3, name: "Американо", description: "Крепкий американо", price: 150, category: "coffee"},
        {id: 4, name: "Эспрессо", description: "Двойной эспрессо", price: 120, category: "coffee"},
        {id: 5, name: "Раф", description: "Ванильный раф с карамелью", price: 220, category: "coffee"},
        {id: 6, name: "Чай черный", description: "Ассам с бергамотом", price: 150, category: "tea"},
        {id: 7, name: "Круассан", description: "Свежий круассан с шоколадом", price: 120, category: "bakery"},
        {id: 8, name: "Чизкейк", description: "Нью-йоркский чизкейк", price: 250, category: "dessert"},
        {id: 9, name: "Сэндвич", description: "С курицей и овощами", price: 200, category: "food"},
    ];
}

function displayMenu(items) {
    const container = document.getElementById('menu-items');
    container.innerHTML = '';

    items.forEach(item => {
        const cartItem = cart.find(ci => ci.id === item.id);
        const quantity = cartItem ? cartItem.quantity : 0;

        const itemElement = document.createElement('div');
        itemElement.className = 'menu-item';
        itemElement.innerHTML = `
            <h3>${item.name}</h3>
            <p class="description">${item.description}</p>
            <div class="price">${item.price} ₽</div>
            <div class="item-actions">
                <div class="quantity-controls">
                    <button onclick="updateQuantity(${item.id}, -1)" ${quantity === 0 ? 'disabled' : ''}>-</button>
                    <span>${quantity}</span>
                    <button onclick="updateQuantity(${item.id}, 1)">+</button>
                </div>
                <button onclick="addToCart(${item.id})" class="add-to-cart">
                    ${quantity === 0 ? 'В корзину' : 'Добавить'}
                </button>
            </div>
        `;

        container.appendChild(itemElement);
    });

    updateCheckoutButton();
}

function filterCategory(category) {
    // Обновляем активную вкладку
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    if (category === 'all') {
        displayMenu(menuItems);
    } else {
        const filtered = menuItems.filter(item => item.category === category);
        displayMenu(filtered);
    }
}

function addToCart(itemId) {
    const item = menuItems.find(i => i.id === itemId);
    const existingItem = cart.find(i => i.id === itemId);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: item.id,
            name: item.name,
            price: item.price,
            quantity: 1
        });
    }

    saveCart();
    updateCartCount();
    displayMenu(menuItems);
    updateCheckoutButton();
}

function updateQuantity(itemId, delta) {
    const itemIndex = cart.findIndex(i => i.id === itemId);

    if (itemIndex !== -1) {
        cart[itemIndex].quantity += delta;

        if (cart[itemIndex].quantity <= 0) {
            cart.splice(itemIndex, 1);
        }

        saveCart();
        updateCartCount();
        displayMenu(menuItems);
        updateCheckoutButton();

        if (document.getElementById('cart-modal').style.display === 'block') {
            displayCart();
        }
    }
}

function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

function updateCartCount() {
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    document.getElementById('cart-count').textContent = total;
}

function updateCheckoutButton() {
    const btn = document.getElementById('checkout-btn');
    const hasItems = cart.length > 0;
    btn.disabled = !hasItems;
    btn.textContent = hasItems
        ? `Перейти к оформлению (${cart.reduce((sum, item) => sum + item.quantity, 0)} товаров)`
        : 'Перейти к оформлению';
}

function openCart() {
    document.getElementById('cart-modal').style.display = 'block';
    displayCart();
}

function closeCart() {
    document.getElementById('cart-modal').style.display = 'none';
}

function displayCart() {
    const container = document.getElementById('cart-items');
    const totalElement = document.getElementById('total-amount');

    if (cart.length === 0) {
        container.innerHTML = '<p class="empty-cart">Корзина пуста</p>';
        totalElement.textContent = '0';
        return;
    }

    let total = 0;
    let html = '';

    cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;

        html += `
            <div class="cart-item">
                <div class="cart-item-info">
                    <h4>${item.name}</h4>
                    <p>${item.price} ₽ × ${item.quantity} = ${itemTotal} ₽</p>
                </div>
                <div class="cart-item-actions">
                    <button onclick="updateQuantity(${item.id}, -1)">-</button>
                    <span>${item.quantity}</span>
                    <button onclick="updateQuantity(${item.id}, 1)">+</button>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
    totalElement.textContent = total;
}

function clearCart() {
    if (confirm('Очистить корзину?')) {
        cart = [];
        saveCart();
        updateCartCount();
        displayCart();
        displayMenu(menuItems);
        closeCart();
    }
}

function scheduleOrder() {
    document.getElementById('time-selection').style.display = 'block';
}

function confirmTime() {
    const timeInput = document.getElementById('scheduled-time');
    scheduledTime = timeInput.value;

    if (scheduledTime) {
        alert(`Заказ будет приготовлен к ${scheduledTime}`);
        document.getElementById('time-selection').style.display = 'none';
    } else {
        alert('Пожалуйста, выберите время');
    }
}

function cancelTime() {
    document.getElementById('time-selection').style.display = 'none';
    scheduledTime = null;
}

function openCheckout() {
    // Сохраняем данные в localStorage для передачи на страницу оформления
    localStorage.setItem('checkoutData', JSON.stringify({
        cart: cart,
        total: cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
        scheduledTime: scheduledTime
    }));

    // Переходим на страницу оформления
    window.location.href = 'checkout.html';
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', loadMenu);

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('cart-modal');
    if (event.target === modal) {
        closeCart();
    }
}