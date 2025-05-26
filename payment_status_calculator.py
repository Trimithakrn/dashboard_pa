import pandas as pd
from datetime import datetime

def preprocess(df):
    # Konversi tanggal ke datetime
    df["tgl_lunas"] = pd.to_datetime(df["tgl_lunas"], errors="coerce")
    df["tgl_tenggat"] = pd.to_datetime(df["tgl_tenggat"], errors="coerce")

    # Buat kolom aktual dan status
    def hitung_status(row):
        if pd.isna(row["tgl_lunas"]):
            return 2, "Belum Dibayar"
        elif row["tgl_lunas"] <= row["tgl_tenggat"]:
            return 0, "Tepat Waktu"
        else:
            return 1, "Terlambat"

    df[["aktual", "status"]] = df.apply(
        lambda row: pd.Series(hitung_status(row)), axis=1)

    return df