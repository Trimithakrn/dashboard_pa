import psycopg2
from psycopg2.extras import RealDictCursor

# Konfigurasi koneksi database
DB_CONFIG = {
    "dbname": "history-pembayaran",
    "user": "postgres",
    "password": "Trimitha",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def fetch_data(query):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data
