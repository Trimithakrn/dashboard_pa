import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")

st.sidebar.title("Menu")
st.sidebar.markdown("Selamat datang di aplikasi interaktif PDAM Surya Sembada")

nav_selection = st.sidebar.radio(
    "Pilih Menu",
    ("Dashboard Pola Pembayaran Pelanggan", "Layanan Monitoring Pelanggan", "Indikasi Pelanggan Terlambat")
)

@st.cache_data
def get_data(thbl):
    if not thbl:
        return pd.DataFrame()
    try:
        url = f"http://127.0.0.1:5000/get_data?thbl={thbl}"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Gagal mengambil data: {e}")
        return pd.DataFrame()

def get_summary(thbl):
    if not thbl:
        return None
    try:
        response = requests.get(f"http://127.0.0.1:5000/get_summary?thbl={thbl}", timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Gagal mengambil ringkasan: {e}")
        return None

@st.cache_data
def get_summary_thbl():
    try:
        response = requests.get("http://127.0.0.1:5000/get_summary_thbl", timeout=60)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Gagal mengambil data: {e}")
        return pd.DataFrame()

if nav_selection == 'Dashboard Pola Pembayaran Pelanggan':
    st.title("Dashboard Pola Pembayaran Pelanggan PDAM Surya Sembada")
    # Tabs for different views
    tab1, tab2 = st.tabs(["Pola Pembayaran per Bulan", "Pola Pembayaran per Kategori"])

    with tab1:
        selected_month = st.text_input("📅 Masukkan Kode Bulan (YYYYMM)", value="202401")

        if selected_month:
            summary_data = get_summary(selected_month)
            if summary_data:
                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Total Pendapatan (Rp)", f"{summary_data.get('total_revenue', 0):,}")
                col2.metric("👥 Total Pelanggan", f"{summary_data.get('total_customers', 0)}")
                col3.metric("⏳ Total Keterlambatan", f"{summary_data.get('total_late', 0)}")

            data = get_data(selected_month)
            if not data.empty:
                col4, col5 = st.columns(2)
                with col4:
                    # Pastikan zona dalam format string
                    data['zona'] = data['zona'].astype(str)
                    # Hitung jumlah pelanggan per zona dan status
                    status_counts = data.groupby(['zona', 'status']).size().reset_index(name='Counts')
                    # Hitung total kerugian per zona (hanya untuk 'Belum Dibayar')
                    data['kerugian'] = data['rp_tagihan'].where(data['status'] == 'Belum Dibayar', 0)
                    kerugian_per_zona = data.groupby('zona')['kerugian'].sum().reset_index()
                    # Gabungkan data jumlah pelanggan dan kerugian
                    status_counts = status_counts.merge(kerugian_per_zona, on="zona", how="left")
                    # Urutkan zona berdasarkan angka jika memungkinkan
                    zona_sorted = sorted(status_counts['zona'].unique(), key=lambda x: int(x) if x.isdigit() else x)
                    # Pilih hanya beberapa zona agar tidak terlalu padat
                    if len(zona_sorted) > 30:
                        zona_sorted = zona_sorted[::2]
                    # Buat bar chart
                    fig1 = px.bar(
                        status_counts,
                        x='zona',
                        y='Counts',  
                        color='status',
                        color_discrete_map={'Terlambat': 'brown', 'Tepat Waktu': 'skyblue', 'Belum Dibayar': 'red'},
                        title="Grafik Wilayah Pelanggan (Jumlah)",
                        labels={'zona': 'Zona', 'Counts': 'Jumlah Pelanggan'},
                        hover_data={'Counts': ':,.0f', 'kerugian': ':,.0f'},  
                        category_orders={"zona": zona_sorted}  
                    )
                    # Atur tampilan agar lebih rapi
                    fig1.update_layout(
                        width=900,
                        height=400,
                        xaxis=dict(
                            title="ZONA",
                            type='category',
                            tickangle=-45  
                        ),
                        yaxis=dict(
                            title="Jumlah Pelanggan"
                        ),
                        legend_title="Status Pembayaran",
                        barmode='group',
                        bargap=0.2,
                        bargroupgap=0.1
                    )
                    st.plotly_chart(fig1, use_container_width=False)

                    # Hitung total pelanggan per status
                    status_total = status_counts.groupby('status')['Counts'].sum().reset_index()
                    # Ambil status dominan
                    status_dominan = status_total.loc[status_total['Counts'].idxmax(), 'status']
                    # Total pelanggan Terlambat
                    total_terlambat = status_total[status_total['status'] == 'Terlambat']['Counts'].values[0] if 'Terlambat' in status_total['status'].values else 0
                    # Zona dengan pelanggan Terlambat terbanyak
                    zona_terlambat = status_counts[status_counts['status'] == 'Terlambat']
                    if not zona_terlambat.empty:
                        zona_terlambat_terbanyak = zona_terlambat.loc[zona_terlambat['Counts'].idxmax()]
                        zona_terlambat_nama = zona_terlambat_terbanyak['zona']
                        zona_terlambat_jumlah = zona_terlambat_terbanyak['Counts']
                    else:
                        zona_terlambat_nama = "-"
                        zona_terlambat_jumlah = 0
                    
                    def generateDetailDesc(String : status_dominan): # type: ignore
                        if (status_dominan == 'Tepat Waktu'):
                            return 'Dibuktikan dengan mayoritas tinggi grafik berwarna biru lebih tinggi daripada warna lainnya.'
                        elif (status_dominan == 'Terlambat'):
                            return 'Dibuktikan dengan mayoritas tinggi grafik berwarna merah gelap lebih tinggi daripada warna lainnya.'
                        else :
                            return 'Dibuktikan dengan mayoritas tinggi grafik berwarna merah teranglebih tinggi daripada warna lainnya.'
                    # Total pelanggan Belum Membayar
                    total_belum_bayar = status_total[status_total['status'] == 'Belum Dibayar']['Counts'].values[0] if 'Belum Dibayar' in status_total['status'].values else 0
                    # Tampilkan analisis otomatis
                    st.markdown("### Analisa Wilayah:")
                    st.markdown(f"""
                    - 📊 Sistem mengidentifikasi adanya dominasi status pembayaran **{status_dominan}**. {generateDetailDesc(status_dominan)}.
                    - ⏰ Tercatat sebanyak **{int(total_terlambat)} pelanggan terlambat dalam melakukan pembayaran**, dan zona dengan jumlah pelanggan Terlambat terbanyak adalah **Zona {zona_terlambat_nama}** dengan **{int(zona_terlambat_jumlah)} pelanggan**.
                    - 💸 Selain itu, terdapat sebanyak **{int(total_belum_bayar)} pelanggan yang masih Belum Membayar** tagihan mereka.
                    """)

                    # Pastikan kolom SUBKELOMPOK dalam format string
                    data['subkelompok'] = data['subkelompok'].astype(str)

                    # Hitung jumlah pelanggan per SUBKELOMPOK dan Status
                    subkelompok_counts = data.groupby(['subkelompok', 'status']).size().reset_index(name='Counts')

                    # Urutkan SUBKELOMPOK agar tampilan lebih rapi
                    subkelompok_sorted = sorted(subkelompok_counts['subkelompok'].unique())

                    # Buat grafik batang jumlah pelanggan per SUBKELOMPOK
                    fig2 = px.bar(
                        subkelompok_counts,
                        x='subkelompok',
                        y='Counts',
                        color='status',
                        title="Grafik Status Pembayaran per SUBKELOMPOK",
                        labels={'subkelompok': 'Subkelompok', 'Counts': 'Jumlah Pelanggan'},
                        color_discrete_map={'Terlambat': 'brown', 'Tepat Waktu': 'skyblue', 'Belum Dibayar': 'red'},
                        category_orders={"subkelompok": subkelompok_sorted}  # Menjaga urutan SUBKELOMPOK
                    )

                    # Atur tampilan grafik
                    fig2.update_layout(
                        width=900,
                        height=600,
                        xaxis=dict(title="Subkelompok", tickangle=-45),
                        yaxis=dict(title="Jumlah Pelanggan"),
                        legend_title="Status Pembayaran",
                        barmode='group',
                        bargap=0.2,
                        bargroupgap=0.1
                    )

                    # Tampilkan grafik di Streamlit
                    st.plotly_chart(fig2, use_container_width=False)

                    # Hitung total pelanggan per status di semua subkelompok
                    sub_status_total = subkelompok_counts.groupby('status')['Counts'].sum().reset_index()

                    # Ambil status dominan secara keseluruhan
                    sub_status_dominan = sub_status_total.loc[sub_status_total['Counts'].idxmax(), 'status']

                    # Total pelanggan Terlambat
                    sub_total_terlambat = sub_status_total[sub_status_total['status'] == 'Terlambat']['Counts'].values[0] if 'Terlambat' in sub_status_total['status'].values else 0

                    # Subkelompok dengan pelanggan Terlambat terbanyak
                    sub_terlambat = subkelompok_counts[subkelompok_counts['status'] == 'Terlambat']
                    if not sub_terlambat.empty:
                        sub_terlambat_terbanyak = sub_terlambat.loc[sub_terlambat['Counts'].idxmax()]
                        sub_terlambat_nama = sub_terlambat_terbanyak['subkelompok']
                        sub_terlambat_jumlah = sub_terlambat_terbanyak['Counts']
                    else:
                        sub_terlambat_nama = "-"
                        sub_terlambat_jumlah = 0

                    # Total pelanggan Belum Membayar
                    sub_total_belum_bayar = sub_status_total[sub_status_total['status'] == 'Belum Dibayar']['Counts'].values[0] if 'Belum Dibayar' in sub_status_total['status'].values else 0

                    # Tampilkan analisis otomatis berdasarkan subkelompok
                    st.markdown("### Analisa Subkelompok:")
                    st.markdown(f"""
                    - 📊 Dari grafik status pembayaran per subkelompok, sistem mendeteksi dominasi status pembayaran **{sub_status_dominan}**, yang menunjukkan pola perilaku pembayaran yang khas di beberapa kategori pelanggan.
                    - ⏰ Tercatat sebanyak **{int(sub_total_terlambat)} pelanggan mengalami keterlambatan pembayaran**, dengan jumlah terbanyak berasal dari **Subkelompok {sub_terlambat_nama}** sebanyak **{int(sub_terlambat_jumlah)} pelanggan**.
                    - 💸 Selain itu, terdapat **{int(sub_total_belum_bayar)} pelanggan yang belum membayar** tagihan mereka.
                    """)

                with col5:
                    status_counts = data.groupby('status')['no_plg'].nunique().reset_index()
                    status_counts.columns = ['status', 'Jumlah Pelanggan']

                    fig2 = px.pie(
                        status_counts, names='status', values='Jumlah Pelanggan',
                        title="Status Pembayaran", color='status',
                        color_discrete_map={'Terlambat': 'brown', 'Tepat Waktu': 'skyblue'}
                    )
                    fig2.update_traces(textinfo='percent+label')
                    fig2.update_layout(
                        height= 400  
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    # Hitung total jumlah pelanggan per status
                    status_counts = data.groupby('status')['no_plg'].nunique().reset_index()
                    status_counts.columns = ['status', 'Jumlah Pelanggan']
                    total_pelanggan = status_counts['Jumlah Pelanggan'].sum()

                    # Hitung proporsi per status
                    status_counts['Persentase'] = (status_counts['Jumlah Pelanggan'] / total_pelanggan * 100).round(2)

                    # Ambil masing-masing nilai
                    terlambat_row = status_counts[status_counts['status'] == 'Terlambat']
                    tepat_row = status_counts[status_counts['status'] == 'Tepat Waktu']

                    jml_terlambat = int(terlambat_row['Jumlah Pelanggan'].values[0]) if not terlambat_row.empty else 0
                    persen_terlambat = float(terlambat_row['Persentase'].values[0]) if not terlambat_row.empty else 0

                    jml_tepat = int(tepat_row['Jumlah Pelanggan'].values[0]) if not tepat_row.empty else 0
                    persen_tepat = float(tepat_row['Persentase'].values[0]) if not tepat_row.empty else 0

                    # Analisis otomatis pie chart
                    st.markdown("### Analisa Status Pembayaran:")
                    st.markdown(f"""
                    - 📈 Dari grafik pie status pembayaran, distribusi pelanggan terlihat cukup jelas: **{jml_tepat} pelanggan** atau **{persen_tepat:.2f}%** membayar **tepat waktu**, sementara **{jml_terlambat} pelanggan** atau **{persen_terlambat:.2f}%** mengalami **keterlambatan pembayaran**.
                    - ✅ Temuan ini menunjukkan bahwa tingkat kedisiplinan pembayaran pelanggan berada pada **level {'baik' if persen_tepat >= 70 else 'perlu perhatian'}**.
                    """)

                    # ambil summary thbl
                    summary_df = get_summary_thbl()
                    # Ubah format bulan agar lebih terbaca (YYYY-MM)
                    summary_df["thbl"] = summary_df["thbl"].astype(str).apply(lambda x: f"{x[:4]}-{x[4:]}")
                    # Konversi ke format numerik untuk visualisasi
                    for col in ["tepat_waktu", "terlambat", "belum_dibayar"]:
                        summary_df[col] = pd.to_numeric(summary_df[col])
                    # Grafik Tren Pembayaran
                    fig4 = px.line(
                        summary_df.melt(id_vars=["thbl"], var_name="Status", value_name="Jumlah"),
                        x="thbl", y="Jumlah", color="Status",
                        title="Tren Jumlah Pelanggan Berdasarkan Status Pembayaran",
                        markers=True,
                        color_discrete_map={'Terlambat': 'brown', 'Tepat Waktu': 'skyblue', 'Belum Dibayar': 'red'}
                    )
                    fig4.update_layout(
                        width=900, height=600,
                        xaxis_title="Periode (YYYY-MM)",
                        yaxis_title="Jumlah Pelanggan",
                        xaxis=dict(tickangle=-45)
                    )
                    st.plotly_chart(fig4, use_container_width=True)

                    # Hitung rata-rata jumlah pelanggan per status
                    avg_tepat = summary_df["tepat_waktu"].mean()
                    avg_terlambat = summary_df["terlambat"].mean()
                    avg_belum_dibayar = summary_df["belum_dibayar"].mean()
                    total_avg = avg_tepat + avg_terlambat + avg_belum_dibayar

                    # Hitung persentase
                    persen_tepat = (avg_tepat / total_avg) * 100 if total_avg > 0 else 0
                    persen_terlambat = (avg_terlambat / total_avg) * 100 if total_avg > 0 else 0
                    persen_belum_dibayar = (avg_belum_dibayar / total_avg) * 100 if total_avg > 0 else 0

                    # Deteksi tren (contoh: perbandingan periode terakhir vs periode sebelumnya)
                    if len(summary_df) >= 2:
                        latest_tepat = summary_df["tepat_waktu"].iloc[-1]
                        prev_tepat = summary_df["tepat_waktu"].iloc[-2]
                        tren_tepat = "meningkat" if latest_tepat > prev_tepat else "menurun" if latest_tepat < prev_tepat else "stabil"
                    else:
                        tren_tepat = "tidak cukup data untuk tren"

                    # Narasi analisis
                    st.markdown("### Analisa Tren per-Bulan:")
                    st.markdown(f"""
                    - 📊 Dari grafik tren bulanan, rata-rata pelanggan yang membayar tepat waktu adalah **{avg_tepat:.0f} pelanggan** atau **{persen_tepat:.2f}%** dari total pelanggan.
                    - ⏰ Sementara itu, rata-rata pelanggan **terlambat mencapai {avg_terlambat:.0f} pelanggan ({persen_terlambat:.2f}%)**, dan rata-rata pelanggan yang **belum membayar** adalah **{avg_belum_dibayar:.0f} pelanggan ({persen_belum_dibayar:.2f}%)**.
                    - ✅ Secara keseluruhan, tingkat kedisiplinan dapat dikatakan **{'baik' if persen_tepat >= 70 else 'perlu perhatian'}**, dengan tren pembayaran tepat waktu yang cenderung **{tren_tepat}** pada periode terakhir.
                    """)

            else:
                st.warning(f"⚠️ Tidak ada data yang tersedia untuk bulan {selected_month}.")

    with tab2:
       # 📡 Mengambil data dari API
        @st.cache_data
        def fetch_data():
            try:
                API_URL = "http://localhost:5000/get_late_subkelompok"
                response = requests.get(API_URL)  # Hapus parameter thbl
                if response.status_code != 200:
                    st.error(f"Error API: {response.status_code}, {response.text}")
                    return pd.DataFrame()  # Return DataFrame kosong jika error
                
                data = response.json()
                return pd.DataFrame(data)  # Konversi data API ke DataFrame
            except Exception as e:
                st.error(f"Error mengambil data: {e}")
                return pd.DataFrame()

        # --- Ambil data ---
        data = fetch_data()

        # Pastikan ada data sebelum lanjut
        if data.empty:
            st.warning("⚠️ Tidak ada data yang tersedia.")
        else:
            # Format THBL
            data['THBL'] = data['thbl'].astype(str)
            data['THBL'] = data['THBL'].str[:4] + "-" + data['THBL'].str[4:]
            data = data.sort_values(by='THBL')

            # ---  Bagian SUBKELOMPOK ---
            st.subheader("Dashboard Pola Pembayaran Pelanggan Terlambat per Subkelompok")
            # Layout 2 Kolom: Grafik Tren & Top 5 Subkelompok Terlambat
            col1, col2 = st.columns(2)
            with col1 :
                # --- Pilih Subkelompok dengan Checklist ---
                subkelompok_list = data['subkelompok'].unique().tolist()
                # Tambahkan opsi "Semua Subkelompok"
                subkelompok_list.insert(0, "Semua Subkelompok")
                selected_subkelompok = st.multiselect(
                    "🔍 Pilih SUBKELOMPOK:",
                    subkelompok_list,
                    default=["Semua Subkelompok"]
                )
                # Filter Data
                if "Semua Subkelompok" in selected_subkelompok:
                    filtered_data = data  # Tampilkan semua data jika "Semua Subkelompok" dipilih
                else:
                    filtered_data = data[data['subkelompok'].isin(selected_subkelompok)]

                # --- Buat Grafik ---
                fig5 = px.line(
                    filtered_data,
                    x='THBL',
                    y='jumlah_pelanggan',
                    color='subkelompok',
                    markers=True,
                    title="📉 Tren Jumlah Pelanggan Terlambat per Subkelompok",
                    labels={'THBL': 'Periode THBL', 'jumlah_pelanggan': 'Jumlah Pelanggan Terlambat', 'subkelompok': 'Subkelompok'}
                )
                st.plotly_chart(fig5, use_container_width=True)
                
                # Hitung total jumlah pelanggan terlambat per subkelompok
                grouped_data = data.groupby("subkelompok")["jumlah_pelanggan"].sum().reset_index()
                # Ambil 5 subkelompok dengan jumlah pelanggan terbanyak
                top_subkelompok = grouped_data.sort_values(by="jumlah_pelanggan", ascending=False).head(5)
                # Urutkan kembali agar yang terbesar di atas (sumbu Y descending)
                top_subkelompok = top_subkelompok.sort_values(by="jumlah_pelanggan", ascending=True)

                # --- Analisa Lonjakan Tertinggi ---
                if not filtered_data.empty:
                    # Hitung total jumlah pelanggan terlambat per bulan
                    monthly_totals = filtered_data.groupby('THBL')['jumlah_pelanggan'].sum().reset_index()

                    # Hitung selisih antar bulan
                    monthly_totals['delta'] = monthly_totals['jumlah_pelanggan'].diff()

                    # Cari lonjakan tertinggi (kenaikan terbesar)
                    max_lonjakan = monthly_totals.sort_values(by='delta', ascending=False).iloc[0]

                    st.markdown("### Analisa :")
                    if pd.notnull(max_lonjakan['delta']) and max_lonjakan['delta'] > 0:
                        st.markdown(f"""
                Lonjakan keterlambatan tertinggi terjadi pada bulan **{max_lonjakan['THBL']}**,  
                dengan peningkatan sebanyak **+{int(max_lonjakan['delta'])} pelanggan** dibanding bulan sebelumnya. Hal ini dikarenakan adanya libur panjang.
                - Subkelompok dengan pelanggan terlambat terbanyak adalah **{top_subkelompok.iloc[0]['subkelompok']}** dengan **{int(top_subkelompok.iloc[0]['jumlah_pelanggan'])} pelanggan**
                - Diikuti oleh:  
                    - **{top_subkelompok.iloc[1]['subkelompok']}**: {int(top_subkelompok.iloc[1]['jumlah_pelanggan'])} pelanggan  
                    - **{top_subkelompok.iloc[2]['subkelompok']}**: {int(top_subkelompok.iloc[2]['jumlah_pelanggan'])} pelanggan
                """)
                    else:
                        st.markdown("Tidak ditemukan lonjakan signifikan pada periode yang dipilih.")
                
            with col2:
                # --- Buat Grafik ---
                fig6 = px.bar(
                    top_subkelompok,
                    x="jumlah_pelanggan",
                    y="subkelompok",
                    orientation="h",
                    text_auto=True,
                    title="Subkelompok dengan Pelanggan Terlambat Terbanyak",
                    labels={"jumlah_pelanggan": "Jumlah Terlambat", "subkelompok": "Subkelompok"},
                    color="jumlah_pelanggan",
                    color_continuous_scale="Reds"
                )
                # --- Atur Ukuran Layout ---
                fig6.update_layout(
                    width=800,   # Ganti sesuai kebutuhan
                    height=500   # Ganti sesuai kebutuhan
                )
                st.plotly_chart(fig6, use_container_width=True)
                # Analisis subkelompok dengan pelanggan terlambat terbanyak
                top_sub = top_subkelompok.sort_values(by="jumlah_pelanggan", ascending=False)
                

                
            # --- Bagian ZONA (Dibawah SUBKELOMPOK) ---
            st.subheader("Dashboard Pola Pembayaran Pelanggan Terlambat per Zona")
            # 📡 Mengambil data dari API
            @st.cache_data
            def get_zona():
                try:
                    API_URL = "http://localhost:5000/get_late_zona"
                    response = requests.get(API_URL)  # Hapus parameter thbl
                    if response.status_code != 200:
                        st.error(f"Error API: {response.status_code}, {response.text}")
                        return pd.DataFrame()  # Return DataFrame kosong jika error
                    
                    data = response.json()
                    return pd.DataFrame(data)  # Konversi data API ke DataFrame
                except Exception as e:
                    st.error(f"Error mengambil data: {e}")
                    return pd.DataFrame()
            # --- Ambil data ---
            data = get_zona()
            # Layout 2 Kolom: Grafik Tren & Top 5 Zona Terlambat
            col3, col4 = st.columns(2)

            with col3:
                # --- Pilih zona dengan Checklist ---
                zona_list = data['zona'].unique().tolist()
                # Tambahkan opsi "Semua zona"
                zona_list.insert(0, "Semua zona")
                selected_zona = st.multiselect(
                    "🔍 Pilih zona:",
                    zona_list,
                    default=["Semua zona"]
                )
                # Filter Data
                if "Semua zona" in selected_zona:
                    filtered_data = data  # Tampilkan semua data jika "Semua zona" dipilih
                else:
                    filtered_data = data[data['zona'].isin(selected_zona)]

                # --- Buat Grafik ---
                fig7 = px.line(
                    filtered_data,
                    x='thbl',
                    y='jumlah_pelanggan',
                    color='zona',
                    markers=True,
                    title="📉 Tren Jumlah Pelanggan Terlambat per zona",
                    labels={'thbl': 'Periode THBL', 'jumlah_pelanggan': 'Jumlah Pelanggan Terlambat', 'zona': 'zona'}
                )
                st.plotly_chart(fig7, use_container_width=True)

                # --- Analisa Lonjakan Tertinggi ---
                # Hitung total jumlah pelanggan terlambat per zona
                grouped_data = data.groupby("zona")["jumlah_pelanggan"].sum().reset_index()

                # Ambil 5 zona dengan jumlah pelanggan terbanyak
                top_zona = grouped_data.sort_values(by="jumlah_pelanggan", ascending=False).head(3)

                # Urutkan kembali agar yang terbesar di atas (sumbu Y descending di Plotly)
                top_zona = top_zona.sort_values(by="jumlah_pelanggan", ascending=True)
                if not filtered_data.empty:
                    # Hitung total jumlah pelanggan terlambat per bulan
                    monthly_totals = filtered_data.groupby('thbl')['jumlah_pelanggan'].sum().reset_index()

                    # Hitung selisih antar bulan
                    monthly_totals['delta'] = monthly_totals['jumlah_pelanggan'].diff()

                    # Cari lonjakan tertinggi (kenaikan terbesar)
                    max_lonjakan = monthly_totals.sort_values(by='delta', ascending=False).iloc[0]

                    st.markdown("### Analisa :")
                    if pd.notnull(max_lonjakan['delta']) and max_lonjakan['delta'] > 0:
                        st.markdown(f"""
                Lonjakan keterlambatan tertinggi terjadi pada bulan **{max_lonjakan['thbl']}**,  
                dengan peningkatan sebanyak **+{int(max_lonjakan['delta'])} pelanggan** dibanding bulan sebelumnya. Hal ini dikarenakan adanya libur panjang.
                - **Zona {top_zona.iloc[0]['zona']}**: **{int(top_zona.iloc[0]['jumlah_pelanggan'])} pelanggan terlambat**
                - Diikuti oleh:  
                    - **Zona {top_zona.iloc[1]['zona']}**: {int(top_zona.iloc[1]['jumlah_pelanggan'])} pelanggan  
                    - **Zona {top_zona.iloc[2]['zona']}**: {int(top_zona.iloc[2]['jumlah_pelanggan'])} pelanggan
                """)


        with col4:
            
            fig8 = px.bar(
                top_zona,
                x="jumlah_pelanggan",
                y="zona",
                orientation="h",
                text_auto=True,
                title="Zona dengan Pelanggan Terlambat Terbanyak",
                labels={"jumlah_pelanggan": "Jumlah Terlambat", "zona": "Zona"},
                color="jumlah_pelanggan",
                color_continuous_scale="Reds"
            )

            # Tambahkan pengaturan agar batang lebih tebal
            fig8.update_layout(
                barmode='relative',  # Mode batang tumpang-tindih
                bargap=0.1,  # Jarak antar batang
                bargroupgap=0.05,  # Jarak antar grup batang
            )
            st.plotly_chart(fig8, use_container_width=True)

if nav_selection == "Layanan Monitoring Pelanggan":
    st.title("Layanan Monitoring Pelanggan")
    # Tabs for different views
    tab1, tab2 = st.tabs(["Pelanggan Potensial Terlambat Bayar", "Monitoring Tagihan Pelanggan PDAM Surya Sembada Kota Surabaya"])
    with tab1:
        # Ambil opsi thbl dari API Flask
        @st.cache_data
        def get_thbl_options():
            response = requests.get("http://localhost:5000/get_thbl_options")
            if response.status_code == 200:
                return response.json()
            return []

        thbl_options = get_thbl_options()

        # Tampilkan dropdown jika tersedia
        if thbl_options:
            selected_thbl = st.selectbox("Pilih Bulan-Tahun (thbl):", thbl_options)

            # Ambil data sesuai pilihan
            response = requests.get(f"http://localhost:5000/get_prediksi_thbl?thbl={selected_thbl}")
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    df = df[["no_plg", "thbl", "zona", "subkelompok", "prediksi_selisih"]]
                    df = df.sort_values(by="prediksi_selisih", ascending=False)
                    st.dataframe(df, use_container_width=True, width=800)

                    # Buat data summary untuk grafik
                    zone_counts = df.groupby("zona").size().reset_index(name="Jumlah Pelanggan")
                    subkelompok_counts = df.groupby("subkelompok").size().reset_index(name="Jumlah Pelanggan")
                    
                    st.markdown("### Insight Grafik Berdasarkan Zona dan Subkelompok")
                    # Buat dua kolom untuk menampilkan grafik berdampingan
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_zone = px.bar(
                            zone_counts,
                            x="zona",
                            y="Jumlah Pelanggan",
                            title="Jumlah Pelanggan per Zona",
                            color="zona",
                            labels={"zona": "Zona", "Jumlah Pelanggan": "Jumlah Pelanggan"},
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_zone, use_container_width=True)
                    
                    with col2:
                        fig_sub = px.bar(
                            subkelompok_counts,
                            x="subkelompok",
                            y="Jumlah Pelanggan",
                            title="Jumlah Pelanggan per Subkelompok",
                            color="subkelompok",
                            labels={"subkelompok": "Subkelompok", "Jumlah Pelanggan": "Jumlah Pelanggan"},
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_sub, use_container_width=True)

                    # --- Analisa Otomatis untuk Grafik Prediksi Zona dan Subkelompok ---
                    if not zone_counts.empty and not subkelompok_counts.empty:
                        # Zona dan Subkelompok dengan jumlah pelanggan terbanyak
                        top_zona = zone_counts.sort_values(by="Jumlah Pelanggan", ascending=False).iloc[0]
                        top_sub = subkelompok_counts.sort_values(by="Jumlah Pelanggan", ascending=False).iloc[0]

                        st.markdown(f"### Analisa untuk {selected_thbl}")
                        st.markdown(f"""
                                    Berdasarkan prediksi untuk **{selected_thbl}**, berikut insight utama yang dapat diperoleh:
                                    - **Zona dengan jumlah pelanggan terbanyak: Zona {top_zona['zona']}** dengan prediksi **{int(top_zona['Jumlah Pelanggan'])} pelanggan**.
                                    - **Subkelompok dengan jumlah pelanggan terbanyak: {top_sub['subkelompok']}** dengan prediksi **{int(top_sub['Jumlah Pelanggan'])} pelanggan**.
                                    
                                    Zona dan subkelompok tersebut berpotensi menjadi fokus prioritas dalam strategi pelayanan bulan berikutnya karena memiliki angka keterlambatan yang besar.
                        """)

                else:
                    st.warning("Tidak ada data prediksi untuk thbl ini.")
            else:
                st.error("Gagal mengambil data prediksi.")
        else:
            st.warning("Tidak ada data thbl tersedia.")
    with tab2:
        @st.cache_data
        # 🔹 Fungsi Ambil Data Prediksi dari API Flask
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

        # 🔹 Fungsi Update Status
        def update_status_in_db(no_plg, new_status):
            return datetime.today().strftime("%Y-%m-%d") if new_status in ["Tepat Waktu", "Terlambat"] else None

        # 🔹 Simulasi Database
        if "database" not in st.session_state:
            st.session_state.database = {}

        if "enter_pressed" not in st.session_state:
            st.session_state.enter_pressed = False

        # 🔹 Input Nomor Pelanggan
        no_plg = st.text_input("Masukkan Nomor Pelanggan:", value="", key="no_plg")

        if st.button("Search"):
            st.session_state.enter_pressed = True

        # 🔹 Proses setelah tombol pencarian ditekan
        if st.session_state.enter_pressed and no_plg:
            data = get_prediction(no_plg)

            if data:
                df = pd.DataFrame(data)

                # 🔹 Urutkan kolom
                desired_order = [
                    "thbl", "no_plg", "zona", "kd_tarif", "subkelompok", "periode",
                    "awal_tagihan", "tgl_lunas", "tgl_tenggat", "rp_tagihan", "status", "selisih_hari", "prediksi_selisih"
                ]
                df = df[[col for col in desired_order if col in df.columns]]

                # 🔹 Format kolom `thbl`
                if "thbl" in df.columns:
                    df["thbl"] = pd.to_datetime(df["thbl"], format="%Y%m").dt.strftime("%Y-%m")

                # 🔹 Tambahkan kolom dropdown editable untuk status baru
                df["Status Baru"] = df["status"]
                column_config = {
                    "Status Baru": st.column_config.SelectboxColumn(
                        "Status Baru",
                        options=["Belum Dibayar", "Tepat Waktu", "Terlambat"],
                        required=True,
                    )
                }

                # 🔹 Editor untuk update status
                edited_df = st.data_editor(df, column_config=column_config, hide_index=True, use_container_width=True)

                # 🔹 Cek perubahan status
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

                    # 🔹 Tampilkan data yang diperbarui saja
                    updated_df = pd.DataFrame(updated_rows)
                    if not updated_df.empty:
                        st.write("### Hasil Pencarian (Hanya Data yang Diperbarui):")
                        st.dataframe(updated_df.style.hide(axis="index"), use_container_width=True)

                # 🔹 Visualisasi garis tren
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

                # --- Analisa otomatis berdasarkan selisih hari dan prediksi ---
                if not avg_df.empty:
                    # Ambil nilai rata-rata selisih hari terakhir
                    last_row = avg_df.iloc[-1]
                    bulan_terakhir = last_row["thbl"]
                    nilai_aktual = last_row["selisih_hari"]
                    nilai_prediksi = last_row["prediksi_selisih"]

                    status_aktual = "tepat waktu" if nilai_aktual < 15 else "terlambat"
                    status_prediksi = "tepat waktu" if nilai_prediksi < 15 else "terlambat"

                    st.markdown(f"### 🔍 Analisa Pembayaran per Bulan")
                    st.markdown(f"""
                                - Pada bulan **{bulan_terakhir}**, rata-rata pelanggan melakukan pembayaran dengan selisih waktu **{nilai_aktual:.1f} hari**, yang akan dikategorikan sebagai **{status_aktual}**.
                                - Prediksi untuk bulan berikutnya menunjukkan rata-rata selisih hari sebesar **{nilai_prediksi:.1f} hari**, yang diperkirakan akan masuk kategori **{status_prediksi}**.
                                - Pelanggan {no_plg} memiliki pola pembayaran yang **{status_prediksi}**.
                """)
            else:
                st.error("❌ Data tidak ditemukan atau terjadi kesalahan.")

if nav_selection == "Indikasi Pelanggan Terlambat":
    st.title("Indikasi Pelanggan Terlambat")
    def get_pelanggan_belum_bayar_data(api_url="http://localhost:5000/api/pelanggan_belum_bayar"):
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Validasi apakah data berbentuk list of dict
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                df = pd.DataFrame(data)
                return df
            else:
                st.error("Format data dari API tidak sesuai.")
                return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            st.error(f"Gagal mengambil data dari API: {e}")
            return pd.DataFrame()
        except ValueError as e:
            st.error(f"Format JSON tidak valid: {e}")
            return pd.DataFrame()

    # Ambil data
    df_belum_bayar = get_pelanggan_belum_bayar_data()
    # Tabs for different views
    tab1, tab2 = st.tabs(["Data Pelanggan Belum Bayar", "Grafik Pelanggan Belum Bayar"])

    with tab1:
        if not df_belum_bayar.empty:
            # Ubah urutan kolom
            urutan_kolom = ["no_plg", "jumlah_bulan", "subkelompok", "zona"]
            df_belum_bayar = df_belum_bayar[urutan_kolom]
            
            # Urutkan berdasarkan jumlah_bulan dari yang terbanyak
            df_belum_bayar = df_belum_bayar.sort_values(by="jumlah_bulan", ascending=False)

            st.dataframe(df_belum_bayar, use_container_width=True, hide_index=True, height=800)
        else:
            st.warning("Tidak ada data untuk ditampilkan.")

    with tab2:
        if not df_belum_bayar.empty:
            st.subheader("Tren Jumlah Pelanggan Belum Bayar per Zona")

            # --- Pilih zona dengan Checklist ---
            zona_list = df_belum_bayar['zona'].unique().tolist()
            zona_list.sort()
            zona_list.insert(0, "Semua zona")
            selected_zona = st.multiselect(
                "🔍 Pilih zona:",
                zona_list,
                default=["Semua zona"]
            )

            # Filter Data
            if "Semua zona" in selected_zona:
                filtered_data = df_belum_bayar
            else:
                filtered_data = df_belum_bayar[df_belum_bayar['zona'].isin(selected_zona)]

            # Group data
            grouped_df = filtered_data.groupby(['jumlah_bulan', 'zona']).size().reset_index(name='jumlah_pelanggan')

            if not grouped_df.empty:
                # Plot dengan Plotly
                fig = px.line(
                    grouped_df,
                    x='jumlah_bulan',
                    y='jumlah_pelanggan',
                    color='zona',
                    markers=True,
                    title='Jumlah Pelanggan Belum Bayar per Zona dan Jumlah Bulan'
                )
                fig.update_layout(
                    xaxis_title='Jumlah Bulan Menunggak',
                    yaxis_title='Jumlah Pelanggan',
                    legend_title='Zona',
                    hovermode='x unified',
                    yaxis=dict(
                        tickmode='linear',
                        dtick=30 
                    )
                )


                st.plotly_chart(fig, use_container_width=True)
                # --- Analisa per ZONA ---
                if not grouped_df.empty:
                    # Fokus ke jumlah bulan tertinggi
                    max_bulan = grouped_df['jumlah_bulan'].max()
                    data_bulan_tertinggi = grouped_df[grouped_df['jumlah_bulan'] == max_bulan]
                    zona_tertinggi = data_bulan_tertinggi.loc[data_bulan_tertinggi['jumlah_pelanggan'].idxmax()]

                    zona_nama = zona_tertinggi['zona']
                    jumlah_plg = zona_tertinggi['jumlah_pelanggan']
                    st.markdown(f"""
                ⏰ Pelanggan dengan **tunggakan paling lama** tercatat pada periode **{max_bulan} bulan**.

                🏠 Zona dengan jumlah pelanggan **belum bayar terbanyak** pada tunggakan {max_bulan} bulan adalah **Zona {zona_nama}**.

                👥 Total pelanggan di kategori ini: **{jumlah_plg} pelanggan**.

                🚨 Zona {zona_nama} memerlukan perhatian khusus karena menampung pelanggan dengan risiko keterlambatan jangka panjang.
                """)
            else:
                st.info("Tidak ada data yang sesuai dengan filter zona yang dipilih.")
                    # === GRAFIK BERDASARKAN SUBKELOMPOK ===
            st.subheader("Tren Jumlah Pelanggan Belum Bayar per Subkelompok")

            # --- Pilih subkelompok dengan Checklist ---
            subkelompok_list = df_belum_bayar['subkelompok'].unique().tolist()
            subkelompok_list.sort()
            subkelompok_list.insert(0, "Semua subkelompok")
            selected_subkelompok = st.multiselect(
                "🔍 Pilih subkelompok:",
                subkelompok_list,
                default=["Semua subkelompok"]
            )

            # Filter data
            if "Semua subkelompok" in selected_subkelompok:
                filtered_data_sub = df_belum_bayar
            else:
                filtered_data_sub = df_belum_bayar[df_belum_bayar['subkelompok'].isin(selected_subkelompok)]

            # Group data
            grouped_df_sub = filtered_data_sub.groupby(['jumlah_bulan', 'subkelompok']).size().reset_index(name='jumlah_pelanggan')

            if not grouped_df_sub.empty:
                fig2 = px.line(
                    grouped_df_sub,
                    x='jumlah_bulan',
                    y='jumlah_pelanggan',
                    color='subkelompok',
                    markers=True,
                    title='Jumlah Pelanggan Belum Bayar per Subkelompok dan Jumlah Bulan'
                )
                fig2.update_layout(
                    xaxis_title='Jumlah Bulan Menunggak',
                    yaxis_title='Jumlah Pelanggan',
                    legend_title='Subkelompok',
                    hovermode='x unified',
                    yaxis=dict(
                        tickmode='linear',
                        dtick=30
                    )
                )

                st.plotly_chart(fig2, use_container_width=True)

                if not grouped_df_sub.empty:
                    max_bulan_sub = grouped_df_sub['jumlah_bulan'].max()
                    data_bulan_tertinggi_sub = grouped_df_sub[grouped_df_sub['jumlah_bulan'] == max_bulan_sub]
                    sub_tertinggi = data_bulan_tertinggi_sub.loc[data_bulan_tertinggi_sub['jumlah_pelanggan'].idxmax()]

                    sub_nama = sub_tertinggi['subkelompok']
                    jumlah_sub = sub_tertinggi['jumlah_pelanggan']

                    st.markdown("### 📊 Insight Subkelompok (Fokus Tunggakan Terlama)")
                    st.markdown(f"""
                ⏰ Tunggakan terlama yang tercatat adalah selama **{max_bulan_sub} bulan**.

                📌 Subkelompok dengan jumlah pelanggan **belum bayar terbanyak** dalam kategori tunggakan {max_bulan_sub} bulan adalah **{sub_nama}**.

                👥 Jumlah pelanggan dalam kondisi ini mencapai **{jumlah_sub} pelanggan**.

                ⚠️ Subkelompok ini sebaiknya diprioritaskan untuk intervensi karena berisiko tinggi terhadap keterlambatan pembayaran yang kronis.
                """)
            else:
                st.info("Tidak ada data yang sesuai dengan filter subkelompok yang dipilih.")
        else:
            st.warning("Tidak ada data untuk ditampilkan di grafik.")
