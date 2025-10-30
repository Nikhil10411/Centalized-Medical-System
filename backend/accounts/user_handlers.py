# app/accounts/user_handlers.py
from ..database import get_db_connection, close_db_connection

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    close_db_connection(conn)
    return [{"id": user[0], "username": user[1]} for user in users]
