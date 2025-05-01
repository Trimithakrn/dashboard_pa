import streamlit as st
import pandas as pd
import requests
import plotly.express as px

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

def show():
    df_belum_bayar = get_pelanggan_belum_bayar_data()

    # Tabs for different views
    tab1, tab2 = st.tabs(["Data Pelanggan Belum Bayar", "Grafik Pelanggan Belum Bayar"])

    with tab1:
        if not df_belum_bayar.empty:
            df = pd.DataFrame(df_belum_bayar)
            # Ubah urutan kolom
            urutan_kolom = ["no_plg", "jumlah_bulan", "subkelompok", "zona"]
            df = df[urutan_kolom]
            df.rename(columns={
                "no_plg": "Nomor Pelanggan",
                "jumlah_bulan": "Jumlah Bulan Berturut-turut",
                "subkelompok": "Subkelompok",
                "zona": "Zona"
            }, inplace=True)
            df_belum_bayar = df_belum_bayar[urutan_kolom]
            # Urutkan berdasarkan jumlah_bulan dari yang terbanyak
            df_belum_bayar = df_belum_bayar.sort_values(by="jumlah_bulan", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True, height=800)
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
                    title= None
                )
                fig.update_layout(
                    height=500,
                    xaxis_title='Jumlah Bulan Menunggak',
                    yaxis_title='Jumlah Pelanggan',
                    legend_title='Zona',
                    hovermode='x unified',
                    yaxis=dict(
                        tickmode='linear',
                        dtick=50 
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                # --- Analisa per ZONA ---
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
                    title= None
                )
                fig2.update_layout(
                    height=500,
                    xaxis_title='Jumlah Bulan Menunggak',
                    yaxis_title='Jumlah Pelanggan',
                    legend_title='Subkelompok',
                    hovermode='x unified',
                    yaxis=dict(
                        tickmode='linear',
                        dtick=50
                    )
                )

                st.plotly_chart(fig2, use_container_width=True)

                if not grouped_df_sub.empty:
                    max_bulan_sub = grouped_df_sub['jumlah_bulan'].max()
                    data_bulan_tertinggi_sub = grouped_df_sub[grouped_df_sub['jumlah_bulan'] == max_bulan_sub]
                    sub_tertinggi = data_bulan_tertinggi_sub.loc[data_bulan_tertinggi_sub['jumlah_pelanggan'].idxmax()]

                    sub_nama = sub_tertinggi['subkelompok']
                    jumlah_sub = sub_tertinggi['jumlah_pelanggan']
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
