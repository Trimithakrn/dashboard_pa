import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine, text
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
import pickle

# 🔹 Konfigurasi Database
CONFIG = {
    "dbname": "history-pembayaran",
    "user": "postgres",
    "password": "Trimitha",
    "host": "localhost",
    "port": "5432"
}

# 🔹 Fungsi koneksi database
def load_data():
    try:
        engine = create_engine(f'postgresql+psycopg2://{CONFIG["user"]}:{CONFIG["password"]}@{CONFIG["host"]}:{CONFIG["port"]}/{CONFIG["dbname"]}')
        with engine.connect() as conn:
            data = pd.read_sql(text("SELECT * FROM history_pembayaran;"), conn)
        return data
    except Exception as e:
        print(f"❌ Error saat membaca database: {e}")
        return pd.DataFrame()

# 🔹 Transformer 1: Preprocessing Data
class PreprocessingTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X["status_database"] = X["status"]

        X["tgl_lunas"] = pd.to_datetime(X["tgl_lunas"], errors="coerce")
        X["awal_tagihan"] = pd.to_datetime(X["awal_tagihan"], errors="coerce")
        X["tgl_tenggat"] = pd.to_datetime(X["tgl_tenggat"], errors="coerce")

        if "is_prediksi" not in X.columns:
            X["is_prediksi"] = False

        today = pd.to_datetime("today").normalize()
        kondisi_update = (
            X["tgl_lunas"].isna() &
            (X["status_database"] == "Belum Dibayar") &
            (X["is_prediksi"] == False)
        )
        X.loc[kondisi_update, "tgl_lunas"] = today

        X["selisih_hari"] = (X["tgl_lunas"] - X["awal_tagihan"]).dt.days
        X["selisih_hari"] = X["selisih_hari"].fillna(0)

        return X

# 🔹 Transformer 2: Moving Average Calculation & Prediction
class MovingAverageTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        if "is_prediksi" not in X.columns:
            X["is_prediksi"] = False

        # Hitung moving average
        X["prediksi_selisih"] = X.groupby("no_plg")["selisih_hari"].transform(
            lambda x: x.rolling(window=2, min_periods=1).mean()
        )

        X["thbl"] = pd.to_numeric(X["thbl"], errors="coerce")
        X = X.dropna(subset=["thbl"]).astype({"thbl": int})

        # Ambil data terakhir per pelanggan
        df_last = X.loc[X.groupby("no_plg")["thbl"].idxmax()].copy()

        # Hitung bulan berikutnya
        df_last["tahun"] = df_last["thbl"] // 100
        df_last["bulan"] = df_last["thbl"] % 100
        df_last["bulan"] += 1
        df_last.loc[df_last["bulan"] > 12, "tahun"] += 1
        df_last["bulan"] = df_last["bulan"] % 12
        df_last.loc[df_last["bulan"] == 0, "bulan"] = 12
        df_last["thbl"] = df_last["tahun"] * 100 + df_last["bulan"]

        # Atur tanggal tagihan dan tenggat
        df_last["awal_tagihan"] += pd.DateOffset(months=1)
        df_last["tgl_tenggat"] = df_last["awal_tagihan"] + pd.Timedelta(days=20)

        # Status dan prediksi
        df_last["status_database"] = df_last.get("status_database", df_last["status"])
        df_last["status"] = "Belum Dibayar"
        df_last["is_prediksi"] = True

        # Gunakan tanggal hari ini sebagai tgl_lunas untuk prediksi belum dibayar
        today = pd.Timestamp.today().normalize()
        df_last["tgl_lunas"] = today

        # Hitung selisih hari
        df_last["selisih_hari"] = (df_last["tgl_lunas"] - df_last["awal_tagihan"]).dt.days

        # Hapus prediksi lama
        X = X[~X["is_prediksi"]]

        # Gabungkan data aktual dan prediksi baru
        df_final = pd.concat([X, df_last], ignore_index=True).sort_values(by=["no_plg", "thbl"])

        return df_final

# 🔹 Pipeline Prediksi
prediction_pipeline = Pipeline([
    ('preprocessing', PreprocessingTransformer()),
    ('moving_average', MovingAverageTransformer())
])

# 🔹 Fungsi mendapatkan prediksi
def get_prediction():
    data = load_data()
    if data.empty:
        return {"error": "❌ Data tidak ditemukan atau terjadi kesalahan saat membaca database."}

    df_final = prediction_pipeline.fit_transform(data)
    if df_final.empty:
        return {"error": "❌ Prediksi gagal, tidak ada data yang diproses."}

    return df_final

# 🔹 Fungsi simpan ke database
def save_predictions(df):
    try:
        engine = create_engine(f'postgresql+psycopg2://{CONFIG["user"]}:{CONFIG["password"]}@{CONFIG["host"]}:{CONFIG["port"]}/{CONFIG["dbname"]}')

        df["awal_tagihan"] = df["awal_tagihan"].where(pd.notna(df["awal_tagihan"]), None)
        df["tgl_tenggat"] = df["tgl_tenggat"].where(pd.notna(df["tgl_tenggat"]), None)
        df["tgl_lunas"] = df["tgl_lunas"].where(pd.notna(df["tgl_lunas"]), pd.Timestamp.today().normalize())

        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print(f"📦 Menyimpan {len(df)} baris ke database...")
            df.to_sql("prediksi_pembayaran", conn, if_exists="replace", index=False, chunksize=10000)
            print("✅ Data berhasil disimpan ke tabel 'prediksi_pembayaran'.")
    except Exception as e:
        print(f"❌ Error saat menyimpan data: {e}")

# 🔹 Simpan model pipeline
with open("model.pkl", "wb") as f:
    pickle.dump(prediction_pipeline, f)

print("✅ Model pipeline berhasil disimpan sebagai 'model.pkl'")

if __name__ == "__main__":
    df_pred = get_prediction()
    if isinstance(df_pred, dict) and "error" in df_pred:
        print(df_pred["error"])
    else:
        print(f"✅ Prediksi selesai, total {len(df_pred)} baris.")
        save_predictions(df_pred)