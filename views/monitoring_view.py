import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
from PIL import Image

def show():
    tab1, tab2 = st.tabs([
        "Pelanggan Potensial Terlambat Bayar", 
        "Monitoring Tagihan Pelanggan PDAM Surya Sembada Kota Surabaya"
    ])

    with tab1:
        # Baca data ikon sebagai gambar
        icon_person = Image.open("icon/person.png")
        icon_maps = Image.open("icon/maps.png")
        icon_people = Image.open("icon/people.png")

        # CSS untuk shadow dan layout
        st.markdown("""
            <style>
            .title {
                font-size: 16px;
                font-weight: 500;
                color: #333333;
            }
            .value {
                font-size: 24px;
                font-weight: 700;
                margin-top: 6px;
            }
            .desc {
                font-size: 14px;
                color: #666666;
                margin-top: -4px;
            }
            </style>
        """, unsafe_allow_html=True)

        def get_thbl_options():
            response = requests.get("http://localhost:5000/get_thbl_options")
            if response.status_code == 200:
                return response.json()
            return []

        thbl_options = get_thbl_options()

        if thbl_options:
            thbl_options_sorted = sorted(thbl_options, reverse=True)
            selected_thbl = st.selectbox("Pilih Tahun-Bulan", thbl_options_sorted)

            response = requests.get(f"http://localhost:5000/get_prediksi_thbl?thbl={selected_thbl}")
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    df = df[["no_plg", "thbl", "zona", "subkelompok", "prediksi_selisih"]]
                    df = df.sort_values(by="prediksi_selisih", ascending=False)

                    total_no_plg = df["no_plg"].count()
                    zone_counts = df.groupby("zona").size().reset_index(name="Jumlah Pelanggan")
                    subkelompok_counts = df.groupby("subkelompok").size().reset_index(name="Jumlah Pelanggan")

                    top_zona = zone_counts.sort_values(by="Jumlah Pelanggan", ascending=False).iloc[0]
                    top_sub = subkelompok_counts.sort_values(by="Jumlah Pelanggan", ascending=False).iloc[0]

                    # Bagi menjadi 3 kolom
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        cols = st.columns([1, 3])
                        with cols[0]:
                            st.image(icon_people, width=76)
                        with cols[1]:
                            st.markdown('<div class="title">Pelanggan Terlambat</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="value">{total_no_plg:,}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="desc">orang</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with col2:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        cols = st.columns([1, 3])
                        with cols[0]:
                            st.image(icon_maps, width=76)
                        with cols[1]:
                            st.markdown('<div class="title">Zona Terbanyak</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="value">Zona {top_zona["zona"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="desc">{top_zona["Jumlah Pelanggan"]:,} pelanggan</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with col3:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        cols = st.columns([1, 3])
                        with cols[0]:
                            st.image(icon_person, width=76)
                        with cols[1]:
                            st.markdown('<div class="title">Subkelompok Terbanyak</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="value">{top_sub["subkelompok"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="desc">{top_sub["Jumlah Pelanggan"]:,} orang</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Detail Grafik
                    st.markdown("### Detail Grafik")
                    detail_type = st.radio("Pilih tampilan grafik:", ["Zona", "Subkelompok"], horizontal=True)

                    col_grafik, col_analisa = st.columns([3, 2])
                    with col_grafik:
                        if detail_type == "Zona":
                            fig_zone = px.bar(zone_counts, x="zona", y="Jumlah Pelanggan", color="zona",
                                              title="Jumlah Pelanggan per Zona", template="plotly_white")
                            st.plotly_chart(fig_zone, use_container_width=True)
                        else:
                            fig_sub = px.bar(subkelompok_counts, x="subkelompok", y="Jumlah Pelanggan", color="subkelompok",
                                             title="Jumlah Pelanggan per Subkelompok", template="plotly_white")
                            st.plotly_chart(fig_sub, use_container_width=True)

                    with col_analisa:
                        st.markdown("### Analisis Grafik :")
                        if detail_type == "Zona":
                            st.markdown(f"""
                                Sebanyak **{total_no_plg} pelanggan diprediksi akan mengalami keterlambatan** dalam pembayaran tagihan air. Dari seluruh zona yang dianalisis, **Zona {top_zona['zona']} mencatat jumlah tertinggi** dengan {top_zona['Jumlah Pelanggan']} pelanggan yang diprediksi terlambat. Hal ini menunjukkan bahwa Zona {top_zona['zona']} memiliki tingkat potensi keterlambatan yang paling tinggi dan dapat menjadi prioritas dalam penanganan lebih lanjut.
                            """)
                        else :
                            st.markdown(f"""
                                Sebanyak **{total_no_plg} pelanggan diprediksi akan mengalami keterlambatan** dalam pembayaran tagihan air. Dari seluruh subkelompok yang dianalisis, **subkelompok {top_sub['subkelompok']} mencatat jumlah tertinggi** dengan {top_sub['Jumlah Pelanggan']} pelanggan yang diprediksi terlambat. Hal ini menunjukkan bahwa subkelompok {top_sub['subkelompok']}1 memiliki tingkat potensi keterlambatan yang paling tinggi dan dapat menjadi prioritas dalam penanganan lebih lanjut.
                            """)

                    # Tabel Pelanggan
                    st.markdown("### Detail Daftar Pelanggan Berpotensi Terlambat")
                    df_display = df.copy()
                    df_display.columns = [
                        "Nomor Pelanggan", 
                        "Tahun Bulan", 
                        "Zona", 
                        "Subkelompok", 
                        "Prediksi Hari Keterlambatan"
                    ]
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.warning("Tidak ada data prediksi untuk bulan ini.")
            else:
                st.error("Gagal mengambil data dari server.")
        else:
            st.warning("Tidak ada data Tahun-Bulan tersedia.")


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

                df.rename(columns={
                    "thbl": "Bulan Tahun",
                    "no_plg": "Nomor Pelanggan",
                    "zona": "Zona",
                    "kd_tarif": "Kode Tarif",
                    "subkelompok": "Subkelompok",
                    "periode": "Periode",
                    "awal_tagihan": "Awal Tagihan",
                    "tgl_lunas": "Tanggal Lunas",
                    "tgl_tenggat": "Tanggal Tenggat",
                    "rp_tagihan": "Jumlah Tagihan",
                    "status": "Status Pembayaran",
                    "selisih_hari": "Selisih Hari",
                    "prediksi_selisih": "Prediksi Selisih",
                    "Status Baru": "Status Baru"
                }, inplace=True)

                # Format kolom Bulan Tahun
                df["Bulan Tahun"] = df["Bulan Tahun"].astype(str)

                # Simpan df asli (termasuk Nomor Pelanggan)
                df_full = df.copy()

                # Buat df_display tanpa kolom Nomor Pelanggan
                df_display = df.drop(columns=["Nomor Pelanggan"])

                # Atur urutan kolom yang ditampilkan
                desired_order = [
                    "Bulan Tahun", "Zona", "Kode Tarif", "Subkelompok", "Periode",
                    "Awal Tagihan", "Tanggal Lunas", "Tanggal Tenggat", "Jumlah Tagihan",
                    "Status Pembayaran", "Selisih Hari", "Prediksi Selisih", "Status Baru"
                ]
                df_display = df_display[[col for col in desired_order if col in df_display.columns]]

                # Inisialisasi kolom "Status Baru"
                df_display["Status Baru"] = df_display["Status Pembayaran"]

                column_config = {
                    "Status Baru": st.column_config.SelectboxColumn(
                        "Status Baru",
                        options=["Belum Dibayar", "Tepat Waktu", "Terlambat"],
                        required=True,
                    )
                }

                # Tampilkan editor tanpa kolom No Pelanggan
                edited_df = st.data_editor(df_display, column_config=column_config, hide_index=True, use_container_width=True)
                changes = edited_df[edited_df["Status Baru"] != df_display["Status Pembayaran"]]

                # Update jika ada perubahan
                if not changes.empty:
                    updated_rows = []
                    for index, row in changes.iterrows():
                        no_plg = df_full.loc[index, "Nomor Pelanggan"]
                        new_tgl_lunas = update_status_in_db(no_plg, row["Status Baru"])
                        edited_df.at[index, "Tanggal Lunas"] = new_tgl_lunas
                        edited_df.at[index, "Status Pembayaran"] = row["Status Baru"]
                        updated_rows.append(edited_df.iloc[index])

                    st.success("✅ Data berhasil diperbarui.")
                    st.session_state.database[no_plg] = edited_df.to_dict("records")

                    updated_df = pd.DataFrame(updated_rows)
                    if not updated_df.empty:
                        st.write("### Hasil Pencarian (Hanya Data yang Diperbarui):")
                        st.dataframe(updated_df.style.hide(axis="index"), use_container_width=True)

                # Visualisasi jika data ada
                col_grafik, col_analisa = st.columns([2, 2])
                with col_grafik:
                    if not df.empty and all(col in df.columns for col in ["Bulan Tahun", "Selisih Hari", "Prediksi Selisih"]):
                        avg_df = df.groupby("Bulan Tahun")[["Selisih Hari", "Prediksi Selisih"]].mean().reset_index()
                        avg_df = avg_df.sort_values("Bulan Tahun")

                        # Long format
                        df_melt = avg_df.melt(id_vars="Bulan Tahun", value_vars=["Selisih Hari", "Prediksi Selisih"],
                                            var_name="Tipe", value_name="Jumlah Hari")

                        fig = px.line(
                            df_melt,
                            x="Bulan Tahun",
                            y="Jumlah Hari",
                            color="Tipe",
                            markers=True,
                            title="📈 Perbandingan Selisih Hari & Prediksi Selisih per Bulan"
                        )
                        fig.update_traces(
                            selector=dict(name="Selisih Hari"),
                            line=dict(color="blue", dash="solid")
                        )
                        fig.update_traces(
                            selector=dict(name="Prediksi Selisih"),
                            line=dict(color="red", dash="dot")
                        )
                        fig.update_layout(xaxis=dict(type="category"))
                        st.plotly_chart(fig, use_container_width=True)
                with col_analisa:
                    st.markdown("**Analisis Grafik :**")

                    if not df.empty and all(col in df.columns for col in ["Nomor Pelanggan", "Status Pembayaran", "Bulan Tahun"]):
                        df_sorted = df.sort_values(by=["Nomor Pelanggan", "Bulan Tahun"])
                        df_sorted["belum_bayar"] = (df_sorted["Status Pembayaran"] == "Belum Dibayar").astype(int)

                        result = []
                        for nomor, group in df_sorted.groupby("Nomor Pelanggan"):
                            count = 0
                            max_count = 0
                            bulan_terakhir = ""
                            for _, row in group.iterrows():
                                if row["belum_bayar"] == 1:
                                    count += 1
                                    bulan_terakhir = row["Bulan Tahun"]
                                else:
                                    if count > max_count:
                                        max_count = count
                                    count = 0
                            if count > max_count:
                                max_count = count
                            if max_count > 1:
                                result.append((nomor, max_count, bulan_terakhir))

                        if not avg_df.empty:
                            last_row = avg_df.iloc[-1]
                            nilai_prediksi = last_row["Prediksi Selisih"]
                            status_prediksi = "tepat waktu" if nilai_prediksi < 15 else "terlambat"

                            st.markdown(f"""
                                Berdasarkan hasil prediksi pada bulan terakhir yang tersedia, pelanggan diperkirakan akan melakukan pembayaran secara **{status_prediksi}**. 
                                Nilai rata-rata prediksi selisih hari mencapai **{nilai_prediksi:.2f} hari**, yang menjadi indikator potensi keterlambatan pembayaran pada bulan berikutnya.
                            """)

                        if result:
                            nomor, bulan, bulan_terakhir = result[0]  # Ambil informasi pelanggan pertama (karena hanya 1 pelanggan)
                            st.markdown(f"""
                                Pelanggan `{nomor}` belum melakukan pembayaran selama **{bulan} bulan berturut-turut**.
                            """)
                        else:
                            st.markdown("Tidak ditemukan pelanggan yang mengalami keterlambatan pembayaran lebih dari satu bulan secara berturut-turut.")

            else:
                st.error("❌ Data tidak ditemukan atau terjadi kesalahan.")
