from sqlalchemy import create_engine, text

# Konfigurasi koneksi ke database PostgreSQL
DB_CONFIG = {
    "dbname": "history-pembayaran",
    "user": "postgres",
    "password": "Trimitha",
    "host": "localhost",
    "port": "5432"
}

# Bangun database URL untuk SQLAlchemy
DB_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# Buat engine
engine = create_engine(DB_URI)

def insert_to_db(df, table_name="history_pembayaran"):
    if "kode_tagihan" not in df.columns:
        raise ValueError("Data tidak memiliki kolom 'kode_tagihan'.")

    with engine.begin() as conn:  # begin() otomatis handle commit/rollback
        for kode in df["kode_tagihan"].unique():
            print(f"Menghapus data dengan kode_tagihan: {kode}")
            delete_stmt = text(f"DELETE FROM {table_name} WHERE kode_tagihan = :kode")
            result = conn.execute(delete_stmt, {"kode": kode})
            print(f"Baris dihapus: {result.rowcount}")  # Tambahan untuk cek

        df.to_sql(table_name, con=conn, if_exists="append", index=False, method='multi')