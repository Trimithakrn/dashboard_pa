import streamlit as st
import pandas as pd
import requests
import plotly.express as px

def get_pelanggan_belum_bayar_data(api_url="http://localhost:5000/api/pelanggan_belum_bayar"):
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

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

def show():
    df_belum_bayar = get_pelanggan_belum_bayar_data()
    
    st.markdown("### Detail Grafik Pelanggan Belum Bayar")
    detail_type = st.radio("Pilih tampilan grafik:", ["Zona", "Subkelompok"], horizontal=True)

    col_grafik, col_analisa = st.columns([3, 2])

    if df_belum_bayar.empty:
        st.warning("Data tidak tersedia.")
        return

    with col_grafik:
        if detail_type == "Zona":
            zona_list = df_belum_bayar['zona'].dropna().unique().tolist()
            zona_list.sort()
            zona_list.insert(0, "Semua zona")
            selected_zona = st.multiselect("🔍 Pilih zona:", zona_list, default=["Semua zona"])

            filtered_data = df_belum_bayar if "Semua zona" in selected_zona else df_belum_bayar[df_belum_bayar['zona'].isin(selected_zona)]

            grouped_df = filtered_data.groupby(['jumlah_bulan', 'zona']).size().reset_index(name='jumlah_pelanggan')
            if not grouped_df.empty:
                fig = px.line(
                    grouped_df,
                    x='jumlah_bulan',
                    y='jumlah_pelanggan',
                    color='zona',
                    markers=True,
                    title='Jumlah Pelanggan Belum Bayar per Zona'
                )
                fig.update_layout(
                    height=500,
                    xaxis_title='Jumlah Bulan Menunggak',
                    yaxis_title='Jumlah Pelanggan',
                    legend_title='Zona',
                    hovermode='x unified',
                    yaxis=dict(tickmode='linear', dtick=50)
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            subkelompok_list = df_belum_bayar['subkelompok'].dropna().unique().tolist()
            subkelompok_list.sort()
            subkelompok_list.insert(0, "Semua subkelompok")
            selected_subkelompok = st.multiselect("🔍 Pilih subkelompok:", subkelompok_list, default=["Semua subkelompok"])

            filtered_data_sub = df_belum_bayar if "Semua subkelompok" in selected_subkelompok else df_belum_bayar[df_belum_bayar['subkelompok'].isin(selected_subkelompok)]

            grouped_df_sub = filtered_data_sub.groupby(['jumlah_bulan', 'subkelompok']).size().reset_index(name='jumlah_pelanggan')
            if not grouped_df_sub.empty:
                fig2 = px.line(
                    grouped_df_sub,
                    x='jumlah_bulan',
                    y='jumlah_pelanggan',
                    color='subkelompok',
                    markers=True
                )
                fig2.update_layout(
                    height=500,
                    xaxis_title='Jumlah Bulan Menunggak',
                    yaxis_title='Jumlah Pelanggan',
                    legend_title='Subkelompok',
                    hovermode='x unified',
                    yaxis=dict(tickmode='linear', dtick=50)
                )
                st.plotly_chart(fig2, use_container_width=True)

    with col_analisa:
        st.markdown("### Analisis Grafik :")
        if detail_type == "Zona" and not df_belum_bayar.empty:
            grouped_df = df_belum_bayar.groupby(['jumlah_bulan', 'zona']).size().reset_index(name='jumlah_pelanggan')
            max_bulan = grouped_df['jumlah_bulan'].max()
            data_bulan_tertinggi = grouped_df[grouped_df['jumlah_bulan'] == max_bulan]
            zona_tertinggi = data_bulan_tertinggi.loc[data_bulan_tertinggi['jumlah_pelanggan'].idxmax()]
            zona_nama = zona_tertinggi['zona']
            jumlah_plg = zona_tertinggi['jumlah_pelanggan']

            st.markdown(f"""
            Pelanggan dengan tunggakan paling lama tercatat memiliki keterlambatan pembayaran hingga **{max_bulan} bulan**, yang mencerminkan adanya risiko keterlambatan jangka panjang dalam sistem pembayaran.  
            Pada kategori tunggakan selama {max_bulan} bulan ini, **Zona {zona_nama}** menjadi wilayah dengan jumlah pelanggan belum membayar terbanyak.  
            Secara keseluruhan, terdapat sebanyak **{jumlah_plg} pelanggan** dalam kategori ini.  
            Temuan ini menunjukkan bahwa **Zona {zona_nama}** memerlukan perhatian khusus, karena menjadi pusat akumulasi pelanggan dengan potensi keterlambatan yang tinggi dan berkepanjangan.
            """)
        elif detail_type == "Subkelompok" and not df_belum_bayar.empty:
            grouped_df_sub = df_belum_bayar.groupby(['jumlah_bulan', 'subkelompok']).size().reset_index(name='jumlah_pelanggan')
            max_bulan_sub = grouped_df_sub['jumlah_bulan'].max()
            data_bulan_tertinggi_sub = grouped_df_sub[grouped_df_sub['jumlah_bulan'] == max_bulan_sub]
            sub_tertinggi = data_bulan_tertinggi_sub.loc[data_bulan_tertinggi_sub['jumlah_pelanggan'].idxmax()]
            sub_nama = sub_tertinggi['subkelompok']
            jumlah_sub = sub_tertinggi['jumlah_pelanggan']

            st.markdown(f"""
            Pelanggan dengan tunggakan paling lama tercatat memiliki keterlambatan pembayaran hingga **{max_bulan_sub} bulan**, yang mencerminkan adanya risiko keterlambatan jangka panjang dalam sistem pembayaran.  
            Pada kategori tunggakan selama {max_bulan_sub} bulan ini, **Subkelompok {sub_nama}** menjadi kelompok dengan jumlah pelanggan belum membayar terbanyak.  
            Secara keseluruhan, terdapat sebanyak **{jumlah_sub} pelanggan** dalam kategori ini.  
            Temuan ini menunjukkan bahwa **Subkelompok {sub_nama}** memerlukan perhatian khusus, karena berpotensi menyumbang keterlambatan paling signifikan.
            """)

    # Tampilkan tabel
    st.markdown("### Detail Daftar Pelanggan Belum Bayar")
    urutan_kolom = ["no_plg", "jumlah_bulan", "subkelompok", "zona"]
    df = df_belum_bayar[urutan_kolom].copy()
    df.rename(columns={
        "no_plg": "Nomor Pelanggan",
        "jumlah_bulan": "Jumlah Bulan Berturut-turut",
        "subkelompok": "Subkelompok",
        "zona": "Zona"
    }, inplace=True)
    df = df.sort_values(by="Jumlah Bulan Berturut-turut", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True, height=500)
