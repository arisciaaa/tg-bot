import sqlite3
import os

DB_PATH = "storage/users.db"


def get_connection():
    """Возвращает соединение с БД"""
    # Создаём папку storage, если её нет
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться по именам колонок
    return conn


def execute_query(query: str, params=()):
    """Удобная функция для выполнения запросов"""
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def execute_update(query: str, params=()):
    """Для INSERT/UPDATE/DELETE"""
    with get_connection() as conn:
        conn.execute(query, params)
        conn.commit()