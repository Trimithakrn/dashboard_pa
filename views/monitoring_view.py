import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

def show():
    tab1, tab2 = st.tabs([
        "Pelanggan Potensial Terlambat Bayar", 
        "Monitoring Tagihan Pelanggan PDAM Surya Sembada Kota Surabaya"
    ])

    with tab1:
        def get_thbl_options():
            response = requests.get("http://localhost:5000/get_thbl_options")
            if response.status_code == 200:
                return response.json()
            return []

        thbl_options = get_thbl_options()

        if thbl_options:
            # Mengurutkan dari terbesar ke terkecil
            thbl_options_sorted = sorted(thbl_options, reverse=True)
            selected_thbl = st.selectbox("Pilih Bulan-Tahun (thbl):", thbl_options_sorted)

            response = requests.get(f"http://localhost:5000/get_prediksi_thbl?thbl={selected_thbl}")
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    df = df[["no_plg", "thbl", "zona", "subkelompok", "prediksi_selisih"]]
                    df = df.sort_values(by="prediksi_selisih", ascending=False)
                    st.dataframe(df, use_container_width=True)

                    zone_counts = df.groupby("zona").size().reset_index(name="Jumlah Pelanggan")
                    subkelompok_counts = df.groupby("subkelompok").size().reset_index(name="Jumlah Pelanggan")

                    st.markdown("### Insight Grafik Berdasarkan Zona dan Subkelompok")
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_zone = px.bar(zone_counts, x="zona", y="Jumlah Pelanggan", color="zona",
                                          title="Jumlah Pelanggan per Zona", template="plotly_white")
                        st.plotly_chart(fig_zone, use_container_width=True)

                    with col2:
                        fig_sub = px.bar(subkelompok_counts, x="subkelompok", y="Jumlah Pelanggan", color="subkelompok",
                                         title="Jumlah Pelanggan per Subkelompok", template="plotly_white")
                        st.plotly_chart(fig_sub, use_container_width=True)

                    if not zone_counts.empty and not subkelompok_counts.empty:
                        total_no_plg = df["no_plg"].count()
                        top_zona = zone_counts.sort_values(by="Jumlah Pelanggan", ascending=False).iloc[0]
                        top_sub = subkelompok_counts.sort_values(by="Jumlah Pelanggan", ascending=False).iloc[0]
                        st.markdown(f"""
                        **Analisa untuk {selected_thbl}**
                        - **{total_no_plg} pelanggan** diprediksi akan **Terlambat**
                        - Zona yang diprediksi terlambat terbanyak : **Zona {top_zona['zona']}** ({top_zona['Jumlah Pelanggan']} pelanggan)
                        - Subkelompok yang diprediksi terlambat terbanyak: **{top_sub['subkelompok']}** ({top_sub['Jumlah Pelanggan']} pelanggan)
                        """)

                else:
                    st.warning("Tidak ada data prediksi untuk thbl ini.")
            else:
                st.error("Gagal mengambil data prediksi.")
        else:
            st.warning("Tidak ada data thbl tersedia.")

    with tab2:
        def get_prediction(no_plg):
            if not no_plg:
                return None
            try:
                url = f"http://127.0.0.1:5000/get_prediction/{no_plg}"
                response = requests.get(url, timeout=200)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Gagal mengambil data: {e}")
                return None

        def update_status_in_db(no_plg, new_status):
            return datetime.today().strftime("%Y-%m-%d") if new_status in ["Tepat Waktu", "Terlambat"] else None

        if "database" not in st.session_state:
            st.session_state.database = {}

        if "enter_pressed" not in st.session_state:
            st.session_state.enter_pressed = False

        no_plg = st.text_input("Masukkan Nomor Pelanggan:", value="", key="no_plg")
        if st.button("Search"):
            st.session_state.enter_pressed = True

        if st.session_state.enter_pressed and no_plg:
            data = get_prediction(no_plg)

            if data:
                df = pd.DataFrame(data)
                desired_order = [
                    "thbl", "no_plg", "zona", "kd_tarif", "subkelompok", "periode",
                    "awal_tagihan", "tgl_lunas", "tgl_tenggat", "rp_tagihan", "status", "selisih_hari", "prediksi_selisih"
                ]
                df = df[[col for col in desired_order if col in df.columns]]
                if "thbl" in df.columns:
                    df["thbl"] = pd.to_datetime(df["thbl"], format="%Y%m").dt.strftime("%Y-%m")

                df["Status Baru"] = df["status"]
                column_config = {
                    "Status Baru": st.column_config.SelectboxColumn(
                        "Status Baru",
                        options=["Belum Dibayar", "Tepat Waktu", "Terlambat"],
                        required=True,
                    )
                }

                edited_df = st.data_editor(df, column_config=column_config, hide_index=True, use_container_width=True)
                changes = edited_df[edited_df["Status Baru"] != df["status"]]

                if not changes.empty:
                    updated_rows = []
                    for index, row in changes.iterrows():
                        new_tgl_lunas = update_status_in_db(row["no_plg"], row["Status Baru"])
                        edited_df.at[index, "tgl_lunas"] = new_tgl_lunas
                        edited_df.at[index, "status"] = row["Status Baru"]
                        updated_rows.append(edited_df.iloc[index])

                    st.success("✅ Data berhasil diperbarui.")
                    st.session_state.database[no_plg] = edited_df.to_dict("records")

                    updated_df = pd.DataFrame(updated_rows)
                    if not updated_df.empty:
                        st.write("### Hasil Pencarian (Hanya Data yang Diperbarui):")
                        st.dataframe(updated_df.style.hide(axis="index"), use_container_width=True)

                if not df.empty and all(col in df.columns for col in ["thbl", "selisih_hari", "prediksi_selisih"]):
                    avg_df = df.groupby("thbl")[["selisih_hari", "prediksi_selisih"]].mean().reset_index()

                    fig = px.line(
                        avg_df,
                        x="thbl",
                        y=["selisih_hari", "prediksi_selisih"],
                        markers=True,
                        labels={"value": "Jumlah Hari", "thbl": "Bulan (YYYY-MM)"},
                        title="📈 Perbandingan Selisih Hari & Prediksi Selisih per Bulan"
                    )
                    fig.update_traces(line=dict(color="blue"), selector=dict(name="selisih_hari"))
                    fig.update_traces(line=dict(color="red", dash="dash"), selector=dict(name="prediksi_selisih"))
                    fig.update_layout(xaxis=dict(type="category"))
                    st.plotly_chart(fig, use_container_width=True)

                    # Analisa pelanggan yang belum bayar lebih dari 1 bulan
                    if "no_plg" in df.columns and "status" in df.columns and "thbl" in df.columns:
                        # Urutkan berdasarkan pelanggan dan bulan
                        df_sorted = df.sort_values(by=["no_plg", "thbl"])
                        
                        # Tandai baris dengan status "Belum Dibayar"
                        df_sorted["belum_bayar"] = (df_sorted["status"] == "Belum Dibayar").astype(int)

                        # Hitung streak keterlambatan berturut-turut per pelanggan
                        result = []
                        for no_plg, group in df_sorted.groupby("no_plg"):
                            count = 0
                            max_count = 0
                            bulan_terakhir = ""
                            for _, row in group.iterrows():
                                if row["belum_bayar"] == 1:
                                    count += 1
                                    bulan_terakhir = row["thbl"]
                                else:
                                    if count > max_count:
                                        max_count = count
                                    count = 0
                            if count > max_count:
                                max_count = count
                            if max_count > 1:
                                result.append((no_plg, max_count, bulan_terakhir))

                    if not avg_df.empty:
                        last_row = avg_df.iloc[-1]
                        nilai_prediksi = last_row["prediksi_selisih"]
                        status_prediksi = "tepat waktu" if nilai_prediksi < 15 else "terlambat"

                        st.markdown("### 🔍 Analisa Pembayaran per Bulan")
                        st.markdown(f"""
                        - Pada bulan selanjutnya, pelanggan diprediksi akan **{status_prediksi}** dalam melakukan pembayaran.
                        """)
                        for no_plg, bulan, terakhir in result:
                            st.markdown(f"- Pelanggan `{no_plg}` belum membayar selama **{bulan} bulan berturut-turut**, terakhir pada `{terakhir}`.")
            else:
                st.error("❌ Data tidak ditemukan atau terjadi kesalahan.")
