from sqlalchemy import create_engine, text
from sqlalchemy import text

# Konfigurasi koneksi database
DB_CONFIG = {
    "dbname": "history-pembayaran",
    "user": "postgres",
    "password": "Trimitha",
    "host": "localhost",
    "port": "5432"
}

DB_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
engine = create_engine(DB_URI)

def insert_to_db(df, table_name="history_pembayaran"):
    if "kode_tagihan" not in df.columns:
        raise ValueError("Data tidak memiliki kolom 'kode_tagihan'.")

    with engine.begin() as conn:
        total_deleted = 0
        for kode in df["kode_tagihan"].unique():
            delete_stmt = text(f"DELETE FROM {table_name} WHERE kode_tagihan = :kode")
            result = conn.execute(delete_stmt, {"kode": kode})
            total_deleted += result.rowcount

        df.to_sql(table_name, con=conn, if_exists="append", index=False, method='multi')
        return total_deleted

def delete_by_kode_tagihan(kode_tagihan_list):
    if not kode_tagihan_list:
        return 0
    kode_tagihan_list = list(set(kode_tagihan_list))  # hilangkan duplikat jika ada
    with engine.connect() as conn:
        # Gunakan parameter array Postgres, pastikan passing list bukan string
        query = text("""
            DELETE FROM history_pembayaran 
            WHERE kode_tagihan = ANY(:kode_list)
        """)
        result = conn.execute(query, {"kode_list": kode_tagihan_list})
        conn.commit()
        return result.rowcount

