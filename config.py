import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# URL вашего Web App (должен быть HTTPS)
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://yourdomain.com/webapp")

# Настройки базы данных
DATABASE_PATH = "coffee_shop.db"

# Настройки заведений
SHOP_INFO = {
    "name": "Кофейня Уютная",
    "address": "ул. Кофейная, 15",
    "phone": "+7 (999) 123-45-67",
    "working_hours": "8:00 - 22:00",
    "delivery_fee": 150,
    "min_order": 300
}