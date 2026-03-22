from datetime import datetime
from storage.database import get_connection

def init_actions_table():
    """Создаёт таблицу для логирования действий"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp TEXT
            )
        """)


def log_action(user_id: int, action: str):
    """Логирует действие пользователя"""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO user_actions (user_id, action, timestamp)
            VALUES (?, ?, ?)
        """, (
            user_id,
            action,
            datetime.utcnow().isoformat()
        ))


def get_user_actions(user_id: int, limit: int = 50):
    """Возвращает последние действия пользователя"""
    with get_connection() as conn:
        return conn.execute("""
            SELECT action, timestamp FROM user_actions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (user_id, limit)).fetchall()


def get_recent_actions(limit: int = 100):
    """Возвращает последние действия всех пользователей"""
    with get_connection() as conn:
        return conn.execute("""
            SELECT user_id, action, timestamp FROM user_actions 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,)).fetchall()


def cleanup_old_actions(days: int = 30):
    """Удаляет действия старше указанного количества дней"""
    with get_connection() as conn:
        cutoff = datetime.utcnow().isoformat()
        # В реальности нужно вычислять дату, но для примера оставим так
        conn.execute("DELETE FROM user_actions WHERE date(timestamp) < date('now', ?)", (f'-{days} days',))