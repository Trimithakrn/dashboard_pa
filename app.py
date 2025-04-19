from flask import Flask, jsonify, request
import psycopg2
import pandas as pd
from model import get_prediction
import pickle
import traceback
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Konfigurasi koneksi ke database PostgreSQL
DB_CONFIG = {
    "dbname": "history-pembayaran",
    "user": "postgres",
    "password": "Trimitha",
    "host": "localhost",
    "port": "5432"
}

# Fungsi koneksi database
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# 🚀 API untuk Mengambil Daftar Bulan yang Tersedia
@app.route('/get_available_thbl', methods=['GET'])
def get_available_thbl():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT thbl FROM public.history_pembayaran ORDER BY thbl DESC;")
        thbl_list = [row[0] for row in cur.fetchall()]
        cur.close()
        return jsonify(thbl_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# 🚀 API untuk Mengambil Data Pembayaran Berdasarkan Bulan
@app.route('/get_data', methods=['GET'])
def get_data():
    thbl = request.args.get("thbl")
    if not thbl:
        return jsonify({"error": "Parameter 'thbl' diperlukan!"}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM public.history_pembayaran WHERE thbl = %s;", (thbl,))
        data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        return jsonify([dict(zip(columns, row)) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# 🚀 API untuk Mengambil Summary Data Pembayaran
@app.route('/get_summary', methods=['GET'])
def get_summary():
    thbl = request.args.get("thbl")
    if not thbl:
        return jsonify({"error": "Parameter 'thbl' diperlukan!"}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                COALESCE(SUM(rp_tagihan), 0) AS total_revenue,
                COALESCE(COUNT(DISTINCT no_plg), 0) AS total_customers,
                COALESCE(SUM(CASE WHEN status = 'Terlambat' THEN 1 ELSE 0 END), 0) AS total_late
            FROM public.history_pembayaran
            WHERE thbl = %s;
        """, (thbl,))
        data = cur.fetchone()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        return jsonify(dict(zip(columns, data)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# 🚀 API untuk Mengambil Seluruh Data Pembayaran
@app.route('/get_summary_thbl', methods=['GET'])
def get_summary_thbl():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT thbl, tepat_waktu, terlambat, belum_dibayar 
            FROM public.pembayaran_thbl
            ORDER BY thbl DESC;
        """)
        data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        return jsonify([dict(zip(columns, row)) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# 🚀 API untuk Mengambil Data Jumlah Pelanggan Terlambat per Subkelompok
@app.route('/get_late_subkelompok', methods=['GET'])
def get_late_subkelompok():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT thbl, subkelompok, jumlah_pelanggan
            FROM public.jumlah_pelanggan_terlambat_subkelompok
            ORDER BY thbl ASC;
        """)  # Hapus filter WHERE thbl = %s
        data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        return jsonify([dict(zip(columns, row)) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# 🚀 API untuk Mengambil Data Jumlah Pelanggan Terlambat per Zona
@app.route('/get_late_zona', methods=['GET'])
def get_late_zona():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT thbl, zona, jumlah_pelanggan
            FROM public.jumlah_pelanggan_terlambat_zona
            ORDER BY thbl ASC;
        """)  # Hapus filter WHERE thbl = %s
        data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        return jsonify([dict(zip(columns, row)) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

## 🔹 API: Ambil semua prediksi
@app.route('/get_prediction', methods=['GET'])
def predict():
    try:
        print("📥 Menerima permintaan semua prediksi...")
        df_pred = get_prediction()

        if isinstance(df_pred, dict) and "error" in df_pred:
            print("❌ Gagal mengambil data:", df_pred["error"])
            return jsonify(df_pred), 500

        print(f"✅ Mengirim {len(df_pred)} baris prediksi.")
        return jsonify(df_pred.to_dict(orient="records"))

    except Exception as e:
        print("🔥 Terjadi kesalahan:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# prediksi per nomor pelanggan
@app.route('/get_prediction/<no_plg>', methods=['GET'])
def get_prediction(no_plg):
    conn = get_db_connection()
    query = f"SELECT * FROM prediksi_pembayaran WHERE no_plg = '{no_plg}' ORDER BY thbl"
    df = pd.read_sql(query, conn)
    conn.close()

    # 🔧 Konversi semua kolom datetime ke string agar bisa di-serialize
    for col in ["awal_tagihan", "tgl_tenggat", "tgl_lunas"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return jsonify(df.to_dict(orient="records"))

# pelanggan belum bayar
@app.route('/api/pelanggan_belum_bayar', methods=['GET'])
def get_pelanggan_belum_bayar():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM pelanggan_belum_bayar')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(rows)

# Dropdown pilih THBL
@app.route("/get_thbl_options", methods=["GET"])
def get_thbl_options():
    conn = get_db_connection()
    query = """
        SELECT DISTINCT thbl
        FROM prediksi_pembayaran
        WHERE is_prediksi = true
        ORDER BY thbl;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert thbl ke list dan kirim sebagai JSON
    thbl_list = df["thbl"].astype(str).tolist()
    return jsonify(thbl_list)

# Prediksi Belum Bayar Sesuai THBL
@app.route("/get_prediksi_thbl", methods=["GET"])
def get_prediksi_by_thbl():
    thbl = request.args.get("thbl")
    if not thbl:
        return jsonify({"error": "Parameter 'thbl' tidak diberikan."}), 400

    try:
        conn = get_db_connection()
        query = f"""
            SELECT no_plg, thbl, zona, subkelompok, prediksi_selisih
            FROM prediksi_pembayaran
            WHERE is_prediksi = true 
              AND prediksi_selisih > 15
              AND thbl = {thbl}
            ORDER BY no_plg;
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)