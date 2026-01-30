import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, WEBAPP_URL
from database import Database
import json

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class CoffeeBot:
    def __init__(self):
        self.db = Database()
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("menu", self.show_menu))
        self.application.add_handler(CommandHandler("my_orders", self.show_my_orders))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        await self.db.register_user(user.id, user.first_name, user.username)

        keyboard = [
            [InlineKeyboardButton("📋 Меню", callback_data='menu')],
            [InlineKeyboardButton("🛒 Корзина", web_app=WebAppInfo(url=f"{WEBAPP_URL}/cart.html"))],
            [InlineKeyboardButton("📦 Мои заказы", callback_data='my_orders')],
            [InlineKeyboardButton("ℹ️ О нас", callback_data='about')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"☕ Добро пожаловать в нашу кофейню, {user.first_name}!\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню"""
        menu_items = await self.db.get_menu()

        keyboard = []
        for item in menu_items:
            keyboard.append([InlineKeyboardButton(
                f"{item['name']} - {item['price']}₽",
                callback_data=f"item_{item['id']}"
            )])

        keyboard.append([InlineKeyboardButton(
            "🛒 Открыть корзину в Mini App",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}")
        )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "☕ **Наше меню:**\n\n"
            "Выберите позицию или откройте корзину для оформления заказа:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback-запросов"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == 'menu':
            await self.show_menu_callback(query)
        elif data == 'my_orders':
            await self.show_my_orders_callback(query)
        elif data.startswith('item_'):
            item_id = int(data.split('_')[1])
            await self.show_item_details(query, item_id)

    async def show_item_details(self, query, item_id):
        """Показать детали товара"""
        item = await self.db.get_menu_item(item_id)

        text = f"*{item['name']}*\n\n"
        text += f"{item['description']}\n\n"
        text += f"Цена: *{item['price']}₽*\n"

        keyboard = [[
            InlineKeyboardButton("➕ Добавить в корзину", callback_data=f"add_{item_id}"),
            InlineKeyboardButton("⬅️ Назад", callback_data='menu')
        ]]

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def show_my_orders_callback(self, query):
        """Показать заказы пользователя"""
        user_id = query.from_user.id
        orders = await self.db.get_user_orders(user_id)

        if not orders:
            text = "📭 У вас еще нет заказов"
        else:
            text = "📦 *Ваши заказы:*\n\n"
            for order in orders[:5]:  # Показываем последние 5 заказов
                status_emoji = {
                    'pending': '⏳',
                    'preparing': '👨‍🍳',
                    'ready': '✅',
                    'delivered': '🚚',
                    'cancelled': '❌'
                }.get(order['status'], '📝')

                text += f"{status_emoji} *Заказ #{order['id']}*\n"
                text += f"Дата: {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                text += f"Сумма: {order['total_amount']}₽\n"
                text += f"Статус: {order['status']}\n"

                if order['scheduled_time']:
                    text += f"На время: {order['scheduled_time'].strftime('%H:%M')}\n"

                text += "\n"

        keyboard = [[InlineKeyboardButton("🛒 Сделать новый заказ", web_app=WebAppInfo(url=WEBAPP_URL))]]

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def process_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка данных из Web App"""
        data = json.loads(update.message.web_app_data.data)
        user_id = update.effective_user.id

        # Сохранение заказа
        order_id = await self.db.create_order(
            user_id=user_id,
            items=data['items'],
            total_amount=data['total'],
            scheduled_time=data.get('scheduledTime'),
            delivery_type=data.get('deliveryType', 'pickup'),
            address=data.get('address'),
            phone=data.get('phone'),
            notes=data.get('notes')
        )

        # Отправляем подтверждение
        text = f"✅ *Заказ #{order_id} оформлен!*\n\n"
        text += f"Сумма: *{data['total']}₽*\n"

        if data.get('scheduledTime'):
            text += f"Время получения: *{data['scheduledTime']}*\n"

        text += f"\nСтатус заказа можно отслеживать в разделе 'Мои заказы'"

        await update.message.reply_text(text, parse_mode='Markdown')

        # Уведомление администратора
        await self.notify_admin(order_id, data)

    async def notify_admin(self, order_id, order_data):
        """Уведомление администратора о новом заказе"""
        admin_id = "YOUR_ADMIN_ID"  # Замените на ID администратора

        text = f"📦 *Новый заказ #{order_id}*\n\n"
        text += f"Сумма: {order_data['total']}₽\n"
        text += f"Тип: {order_data.get('deliveryType', 'pickup')}\n"

        if order_data.get('scheduledTime'):
            text += f"На время: {order_data['scheduledTime']}\n"

        await self.application.bot.send_message(chat_id=admin_id, text=text, parse_mode='Markdown')

    def run(self):
        """Запуск бота"""
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    bot = CoffeeBot()
    bot.run()