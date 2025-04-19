import streamlit as st
import plotly.express as px
import pandas as pd

def render_perkategori_tab(fetch_data, get_zona):
    data = fetch_data()

    if data.empty:
        st.warning("⚠️ Tidak ada data yang tersedia.")
        return

    data['THBL'] = data['thbl'].astype(str)
    data['THBL'] = data['THBL'].str[:4] + "-" + data['THBL'].str[4:]
    data = data.sort_values(by='THBL')

    st.subheader("Dashboard Pola Pembayaran Pelanggan Terlambat per Subkelompok")
    col1, col2 = st.columns(2)

    with col1:
        subkelompok_list = data['subkelompok'].unique().tolist()
        subkelompok_list.insert(0, "Semua Subkelompok")
        selected_subkelompok = st.multiselect(
            "🔍 Pilih SUBKELOMPOK:",
            subkelompok_list,
            default=["Semua Subkelompok"]
        )

        filtered_data = data if "Semua Subkelompok" in selected_subkelompok else data[data['subkelompok'].isin(selected_subkelompok)]

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

        grouped_data = data.groupby("subkelompok")["jumlah_pelanggan"].sum().reset_index()
        top_subkelompok = grouped_data.sort_values(by="jumlah_pelanggan", ascending=False).head(5)
        top_subkelompok = top_subkelompok.sort_values(by="jumlah_pelanggan", ascending=True)

        monthly_totals = filtered_data.groupby('THBL')['jumlah_pelanggan'].sum().reset_index()
        monthly_totals['delta'] = monthly_totals['jumlah_pelanggan'].diff()

        if not monthly_totals.empty:
            max_lonjakan = monthly_totals.sort_values(by='delta', ascending=False).iloc[0]
            st.markdown("### Analisa:")
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
        fig6.update_layout(width=800, height=500)
        st.plotly_chart(fig6, use_container_width=True)

    st.subheader("Dashboard Pola Pembayaran Pelanggan Terlambat per Zona")
    data = get_zona()

    col3, col4 = st.columns(2)

    with col3:
        zona_list = data['zona'].unique().tolist()
        zona_list.insert(0, "Semua zona")
        selected_zona = st.multiselect(
            "🔍 Pilih zona:",
            zona_list,
            default=["Semua zona"]
        )

        filtered_data = data if "Semua zona" in selected_zona else data[data['zona'].isin(selected_zona)]

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

        grouped_data = data.groupby("zona")["jumlah_pelanggan"].sum().reset_index()
        top_zona = grouped_data.sort_values(by="jumlah_pelanggan", ascending=False).head(3)
        top_zona = top_zona.sort_values(by="jumlah_pelanggan", ascending=True)

        if not filtered_data.empty:
            monthly_totals = filtered_data.groupby('thbl')['jumlah_pelanggan'].sum().reset_index()
            monthly_totals['delta'] = monthly_totals['jumlah_pelanggan'].diff()
            max_lonjakan = monthly_totals.sort_values(by='delta', ascending=False).iloc[0]

            st.markdown("### Analisa:")
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
        fig8.update_layout(barmode='relative', bargap=0.1, bargroupgap=0.05)
        st.plotly_chart(fig8, use_container_width=True)