# database.py
import os
import sqlite3
from dotenv import load_dotenv

# Muat variabel dari .env
load_dotenv()
DB_TYPE = os.getenv("DB_TYPE", "sqlite")

# Lakukan impor dinamis berdasarkan DB_TYPE
if DB_TYPE == "postgresql":
    try:
        import psycopg2
    except ImportError:
        print(
            "ERROR: psycopg2 tidak terinstal. Jalankan 'pip install psycopg2-binary' untuk menggunakan PostgreSQL."
        )
        exit()


def get_db_connection():
    """Membuat dan mengembalikan koneksi ke database yang sesuai."""
    try:
        if DB_TYPE == "postgresql":
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                dbname=os.getenv("DB_NAME"),
            )
            return conn
        else:  # Default ke SQLite
            return sqlite3.connect(os.getenv("DB_NAME", "gaya_san.db"))
    except Exception as e:
        print(f"Error saat menyambungkan ke database: {e}")
        return None


def init_db():
    """Membuat semua tabel jika belum ada (berguna untuk setup awal SQLite)."""
    if DB_TYPE == "sqlite":
        conn = get_db_connection()
        if conn:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS wardrobe (
                        item_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                        item_type TEXT NOT NULL, color TEXT NOT NULL, description TEXT
                    )
                """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ratings (
                        rating_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                        outfit_description TEXT NOT NULL, rating INTEGER NOT NULL
                    )
                """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS preferences (
                        user_id INTEGER PRIMARY KEY, favorite_styles TEXT,
                        favorite_colors TEXT, avoided_items TEXT
                    )
                """
                )
            conn.close()


def execute_query(query, params=None, fetch=None):
    """Fungsi pembantu untuk menjalankan semua jenis query dengan aman."""
    conn = get_db_connection()
    if not conn:
        return [] if fetch else None
    if DB_TYPE == "postgresql":
        query = query.replace("?", "%s")
    result = None
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch == "one":
                result = cursor.fetchone()
            elif fetch == "all":
                result = cursor.fetchall()
            else:
                conn.commit()
    except Exception as e:
        print(f"Query gagal: {e}")
    finally:
        if conn:
            conn.close()
    return result


# --- Fungsi untuk Fitur Bot ---


def add_item_to_wardrobe(user_id, item_type, color, description):
    query = "INSERT INTO wardrobe (user_id, item_type, color, description) VALUES (?, ?, ?, ?)"
    execute_query(query, (user_id, item_type, color, description))


def get_wardrobe_items(user_id):
    query = "SELECT item_type, color, description FROM wardrobe WHERE user_id = ?"
    return execute_query(query, (user_id,), fetch="all")


def save_rating(user_id, outfit_description, rating):
    query = "INSERT INTO ratings (user_id, outfit_description, rating) VALUES (?, ?, ?)"
    execute_query(query, (user_id, outfit_description, rating))


def update_preferences(user_id, styles, colors, avoids):
    if DB_TYPE == "postgresql":
        query = "INSERT INTO preferences (user_id, favorite_styles, favorite_colors, avoided_items) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET favorite_styles = EXCLUDED.favorite_styles, favorite_colors = EXCLUDED.favorite_colors, avoided_items = EXCLUDED.avoided_items"
    else:  # SQLite
        query = "INSERT INTO preferences (user_id, favorite_styles, favorite_colors, avoided_items) VALUES (?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET favorite_styles = excluded.favorite_styles, favorite_colors = excluded.favorite_colors, avoided_items = excluded.avoided_items"
    execute_query(query, (user_id, styles, colors, avoids))


def get_explicit_preferences(user_id):
    query = "SELECT favorite_styles, favorite_colors, avoided_items FROM preferences WHERE user_id = ?"
    return execute_query(query, (user_id,), fetch="one")


def get_user_preferences(user_id):  # Preferensi implisit dari rating
    query = "SELECT outfit_description FROM ratings WHERE user_id = ? AND rating = 1 ORDER BY rating_id DESC LIMIT 5"
    rows = execute_query(query, (user_id,), fetch="all") or []
    return [row[0] for row in rows]
