from datetime import datetime
from storage.database import get_connection


def init_users_table():
    """Создаёт таблицу пользователей, если её нет"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen_at TEXT,
                role TEXT DEFAULT 'simple-user'
            )
        """)


def user_exists(user_id: int) -> bool:
    """Проверяет, существует ли пользователь"""
    with get_connection() as conn:
        result = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return result is not None


def register_user(user):
    """Регистрирует нового пользователя"""
    if user_exists(user.id):
        return False

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, first_seen_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            datetime.utcnow().date().isoformat()
        ))
        return True


def set_admin(user_id: int):
    """Назначает пользователя администратором"""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET role = 'admin' WHERE user_id = ?",
            (user_id,)
        )


def get_user_role(user_id: int) -> str:
    """Возвращает роль пользователя"""
    with get_connection() as conn:
        result = conn.execute(
            "SELECT role FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return result[0] if result else None


def get_all_users():
    """Возвращает список всех пользователей (для админки)"""
    with get_connection() as conn:
        return conn.execute(
            "SELECT user_id, username, role, first_seen_at FROM users ORDER BY first_seen_at DESC"
        ).fetchall()


def get_user_stats() -> dict:
    """Возвращает статистику по пользователям"""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        admins = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        today = datetime.utcnow().date().isoformat()
        new_today = conn.execute(
            "SELECT COUNT(*) FROM users WHERE first_seen_at = ?",
            (today,)
        ).fetchone()[0]

        return {
            "total": total,
            "admins": admins,
            "new_today": new_today
        }