import streamlit as st
import pandas as pd
import io
from datetime import datetime
import uuid

from database import insert_to_db
from payment_status_calculator import preprocess

def show():
    st.markdown("### Unggah Data Pelanggan dari File CSV")
    st.info("Pastikan file CSV Anda memiliki kolom yang sesuai dengan data pelanggan dengan format yang telah disediakan")

    uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("✅ File CSV berhasil diunggah!")
            st.write("📊 Pratinjau Data:")
            st.dataframe(df.head())

            # Tombol untuk memproses data
            if st.button("🚀 Proses & Simpan ke Database"):
                df = preprocess(df)
                insert_to_db(df)
                st.success("✅ Data berhasil diproses dan disimpan ke database!")

                # Simpan ke session history
                upload_info = {
                    "id": str(uuid.uuid4()),
                    "nama_file": uploaded_file.name,
                    "tanggal_unggah": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.upload_history.append(upload_info)

        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file CSV: {e}")
            st.warning("Pastikan format file CSV Anda benar.")

    # 🔽 Contoh format CSV
    sample_data = {
        "kode_tagihan": ["2025012259AA", "2025022260BB", "2025032261CC"],
        "thbl": ["202501", "202502", "202503"],
        "no_plg": ["2259AA", "2260BB", "2261CC"],
        "kd_tarif": ["3.1", "2.2", "1.1"],
        "subkelompok": ["Rumah Menengah", "Niaga Kecil", "Rumah Sederhana"],
        "zona": ["101", "102", "103"],
        "periode": [1, 2, 3],
        "awal_tagihan": ["1/1/2025", "2/1/2025", "3/1/2025"],
        "tgl_lunas": ["1/14/2025", "2/20/2025", "3/18/2025"],
        "tgl_tenggat": ["1/15/2025", "2/15/2025", "3/15/2025"],
        "rp_tagihan": [120000, 150000, 100000]
    }
    df_sample = pd.DataFrame(sample_data)

    csv_buffer = io.StringIO()
    df_sample.to_csv(csv_buffer, index=False)
    csv_string = csv_buffer.getvalue()

    st.download_button(
        label="📥 Unduh Contoh Format CSV",
        data=csv_string,
        file_name="contoh_data_pelanggan_pdam.csv",
        mime="text/csv"
    )

    # Riwayat unggahan
    if 'upload_history' not in st.session_state:
        st.session_state.upload_history = []

    if st.session_state.upload_history:
        st.markdown("### 📚 Riwayat Unggahan")
        history_df = pd.DataFrame(st.session_state.upload_history)
        st.dataframe(history_df[['nama_file', 'tanggal_unggah']], key="upload_history_df")

        st.markdown("**Hapus Riwayat Unggahan:**")
        for i, row in history_df.iterrows():
            col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
            with col1:
                st.write(row['nama_file'])
            with col2:
                st.write(row['tanggal_unggah'])
            with col3:
                if st.button("🗑️ Hapus", key=f"delete_{row['id']}"):
                    st.session_state.upload_history = [
                        item for item in st.session_state.upload_history if item['id'] != row['id']
                    ]
                    st.success(f"Riwayat '{row['nama_file']}' berhasil dihapus.")
                    st.rerun()
    else:
        st.info("Belum ada riwayat unggahan data.")
