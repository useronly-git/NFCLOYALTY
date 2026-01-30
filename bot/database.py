import sqlite3
import aiosqlite
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    def __init__(self, db_path='coffee_shop.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Пользователи
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS users
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY,
                               telegram_id
                               INTEGER
                               UNIQUE,
                               name
                               TEXT,
                               username
                               TEXT,
                               phone
                               TEXT,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            # Меню
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS menu
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               name
                               TEXT
                               NOT
                               NULL,
                               description
                               TEXT,
                               price
                               REAL
                               NOT
                               NULL,
                               category
                               TEXT,
                               available
                               BOOLEAN
                               DEFAULT
                               1,
                               image_url
                               TEXT
                           )
                           ''')

            # Заказы
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS orders
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               user_id
                               INTEGER,
                               total_amount
                               REAL
                               NOT
                               NULL,
                               status
                               TEXT
                               DEFAULT
                               'pending',
                               delivery_type
                               TEXT
                               DEFAULT
                               'pickup',
                               address
                               TEXT,
                               phone
                               TEXT,
                               notes
                               TEXT,
                               scheduled_time
                               TIMESTAMP,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               FOREIGN
                               KEY
                           (
                               user_id
                           ) REFERENCES users
                           (
                               id
                           )
                               )
                           ''')

            # Позиции заказа
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS order_items
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               order_id
                               INTEGER,
                               menu_item_id
                               INTEGER,
                               quantity
                               INTEGER
                               NOT
                               NULL,
                               price
                               REAL
                               NOT
                               NULL,
                               notes
                               TEXT,
                               FOREIGN
                               KEY
                           (
                               order_id
                           ) REFERENCES orders
                           (
                               id
                           ),
                               FOREIGN KEY
                           (
                               menu_item_id
                           ) REFERENCES menu
                           (
                               id
                           )
                               )
                           ''')

            conn.commit()

            # Добавляем тестовые данные в меню
            self._add_sample_data(cursor)

    def _add_sample_data(self, cursor):
        """Добавление тестовых данных в меню"""
        sample_items = [
            ('Капучино', 'Классический капучино с молоком', 180, 'coffee'),
            ('Латте', 'Нежный латте с молочной пенкой', 190, 'coffee'),
            ('Американо', 'Крепкий американо', 150, 'coffee'),
            ('Эспрессо', 'Двойной эспрессо', 120, 'coffee'),
            ('Раф', 'Ванильный раф с карамелью', 220, 'coffee'),
            ('Чай черный', 'Ассам с бергамотом', 150, 'tea'),
            ('Круассан', 'Свежий круассан с шоколадом', 120, 'bakery'),
            ('Чизкейк', 'Нью-йоркский чизкейк', 250, 'dessert'),
            ('Сэндвич', 'С курицей и овощами', 200, 'food'),
        ]

        cursor.execute("SELECT COUNT(*) FROM menu")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO menu (name, description, price, category) VALUES (?, ?, ?, ?)",
                sample_items
            )

    async def register_user(self, telegram_id: int, name: str, username: str = None):
        """Регистрация пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (telegram_id, name, username) VALUES (?, ?, ?)",
                (telegram_id, name, username)
            )
            await db.commit()

    async def get_menu(self) -> List[Dict]:
        """Получение меню"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM menu WHERE available = 1")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_menu_item(self, item_id: int) -> Dict:
        """Получение информации о товаре"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM menu WHERE id = ?", (item_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def create_order(self, user_id: int, items: List[Dict], total_amount: float,
                           scheduled_time: str = None, delivery_type: str = 'pickup',
                           address: str = None, phone: str = None, notes: str = None) -> int:
        """Создание заказа"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем ID пользователя
            cursor = await db.execute(
                "SELECT id FROM users WHERE telegram_id = ?",
                (user_id,)
            )
            user_row = await cursor.fetchone()
            db_user_id = user_row[0] if user_row else None

            if not db_user_id:
                # Создаем пользователя, если его нет
                await self.register_user(user_id, "User")
                cursor = await db.execute(
                    "SELECT id FROM users WHERE telegram_id = ?",
                    (user_id,)
                )
                user_row = await cursor.fetchone()
                db_user_id = user_row[0]

            # Создаем заказ
            cursor = await db.execute('''
                                      INSERT INTO orders
                                      (user_id, total_amount, status, delivery_type, address, phone, notes,
                                       scheduled_time)
                                      VALUES (?, ?, 'pending', ?, ?, ?, ?, ?)
                                      ''',
                                      (db_user_id, total_amount, delivery_type, address, phone, notes, scheduled_time))

            order_id = cursor.lastrowid

            # Добавляем позиции заказа
            for item in items:
                await db.execute('''
                                 INSERT INTO order_items
                                     (order_id, menu_item_id, quantity, price, notes)
                                 VALUES (?, ?, ?, ?, ?)
                                 ''', (order_id, item['id'], item['quantity'], item['price'], item.get('notes')))

            await db.commit()
            return order_id

    async def get_user_orders(self, telegram_id: int) -> List[Dict]:
        """Получение заказов пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                                      SELECT o.*
                                      FROM orders o
                                               JOIN users u ON o.user_id = u.id
                                      WHERE u.telegram_id = ?
                                      ORDER BY o.created_at DESC LIMIT 10
                                      ''', (telegram_id,))

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]