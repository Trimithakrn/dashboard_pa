import streamlit as st
import plotly.express as px
import pandas as pd

def render_perbulan_tab(get_summary, get_data, get_summary_thbl):
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
                # Zona Chart dan Analisis
                data['zona'] = data['zona'].astype(str)
                status_counts = data.groupby(['zona', 'status']).size().reset_index(name='Counts')
                data['kerugian'] = data['rp_tagihan'].where(data['status'] == 'Belum Dibayar', 0)
                kerugian_per_zona = data.groupby('zona')['kerugian'].sum().reset_index()
                status_counts = status_counts.merge(kerugian_per_zona, on="zona", how="left")
                zona_sorted = sorted(status_counts['zona'].unique(), key=lambda x: int(x) if x.isdigit() else x)
                if len(zona_sorted) > 30:
                    zona_sorted = zona_sorted[::2]

                fig1 = px.bar(
                    status_counts,
                    x='zona', y='Counts', color='status',
                    color_discrete_map={'Terlambat': 'brown', 'Tepat Waktu': 'skyblue', 'Belum Dibayar': 'red'},
                    title="Grafik Wilayah Pelanggan (Jumlah)",
                    labels={'zona': 'Zona', 'Counts': 'Jumlah Pelanggan'},
                    hover_data={'Counts': ':,.0f', 'kerugian': ':,.0f'},
                    category_orders={"zona": zona_sorted}
                )
                fig1.update_layout(
                    width=900, height=400,
                    xaxis=dict(title="ZONA", type='category', tickangle=-45),
                    yaxis=dict(title="Jumlah Pelanggan"),
                    legend_title="Status Pembayaran",
                    barmode='group', bargap=0.2, bargroupgap=0.1
                )
                st.plotly_chart(fig1, use_container_width=False)

                status_total = status_counts.groupby('status')['Counts'].sum().reset_index()
                status_dominan = status_total.loc[status_total['Counts'].idxmax(), 'status']
                total_terlambat = status_total[status_total['status'] == 'Terlambat']['Counts'].values[0] if 'Terlambat' in status_total['status'].values else 0
                zona_terlambat = status_counts[status_counts['status'] == 'Terlambat']
                if not zona_terlambat.empty:
                    zona_terlambat_terbanyak = zona_terlambat.loc[zona_terlambat['Counts'].idxmax()]
                    zona_terlambat_nama = zona_terlambat_terbanyak['zona']
                    zona_terlambat_jumlah = zona_terlambat_terbanyak['Counts']
                else:
                    zona_terlambat_nama = "-"
                    zona_terlambat_jumlah = 0

                def generateDetailDesc(status_dominan):
                    if status_dominan == 'Tepat Waktu':
                        return 'Dibuktikan dengan mayoritas tinggi grafik biru.'
                    elif status_dominan == 'Terlambat':
                        return 'Dibuktikan dengan mayoritas grafik merah gelap.'
                    else:
                        return 'Dibuktikan dengan grafik merah terang mendominasi.'

                total_belum_bayar = status_total[status_total['status'] == 'Belum Dibayar']['Counts'].values[0] if 'Belum Dibayar' in status_total['status'].values else 0

                st.markdown("### Analisa Wilayah:")
                st.markdown(f"""
                - 📊 Dominasi status: **{status_dominan}**. {generateDetailDesc(status_dominan)}
                - ⏰ Total keterlambatan: **{int(total_terlambat)} pelanggan**, terutama di Zona **{zona_terlambat_nama}** (**{int(zona_terlambat_jumlah)} pelanggan**).
                - 💸 Belum membayar: **{int(total_belum_bayar)} pelanggan**
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
                # Pie Chart
                status_counts = data.groupby('status')['no_plg'].nunique().reset_index()
                status_counts.columns = ['status', 'Jumlah Pelanggan']

                fig2 = px.pie(
                    status_counts, names='status', values='Jumlah Pelanggan',
                    title="Status Pembayaran", color='status',
                    color_discrete_map={'Terlambat': 'brown', 'Tepat Waktu': 'skyblue'}
                )
                fig2.update_traces(textinfo='percent+label')
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)

                total_pelanggan = status_counts['Jumlah Pelanggan'].sum()
                status_counts['Persentase'] = (status_counts['Jumlah Pelanggan'] / total_pelanggan * 100).round(2)
                terlambat_row = status_counts[status_counts['status'] == 'Terlambat']
                tepat_row = status_counts[status_counts['status'] == 'Tepat Waktu']
                jml_terlambat = int(terlambat_row['Jumlah Pelanggan'].values[0]) if not terlambat_row.empty else 0
                persen_terlambat = float(terlambat_row['Persentase'].values[0]) if not terlambat_row.empty else 0
                jml_tepat = int(tepat_row['Jumlah Pelanggan'].values[0]) if not tepat_row.empty else 0
                persen_tepat = float(tepat_row['Persentase'].values[0]) if not tepat_row.empty else 0

                st.markdown("### Analisa Status Pembayaran:")
                st.markdown(f"""
                - 📈 Tepat waktu: **{jml_tepat} pelanggan ({persen_tepat:.2f}%)**
                - 🔴 Terlambat: **{jml_terlambat} pelanggan ({persen_terlambat:.2f}%)**
                - ✅ Tingkat kedisiplinan: **{'Baik' if persen_tepat >= 70 else 'Perlu perhatian'}**
                """)

                # Tren Bulanan
                summary_df = get_summary_thbl()
                summary_df["thbl"] = summary_df["thbl"].astype(str).apply(lambda x: f"{x[:4]}-{x[4:]}")
                for col in ["tepat_waktu", "terlambat", "belum_dibayar"]:
                    summary_df[col] = pd.to_numeric(summary_df[col])

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

                # Rata-rata tren
                avg_tepat = summary_df["tepat_waktu"].mean()
                avg_terlambat = summary_df["terlambat"].mean()
                avg_belum_dibayar = summary_df["belum_dibayar"].mean()
                total_avg = avg_tepat + avg_terlambat + avg_belum_dibayar

                persen_tepat = (avg_tepat / total_avg) * 100 if total_avg > 0 else 0
                persen_terlambat = (avg_terlambat / total_avg) * 100 if total_avg > 0 else 0
                persen_belum_dibayar = (avg_belum_dibayar / total_avg) * 100 if total_avg > 0 else 0

                if len(summary_df) >= 2:
                    latest_tepat = summary_df["tepat_waktu"].iloc[-1]
                    prev_tepat = summary_df["tepat_waktu"].iloc[-2]
                    tren_tepat = "meningkat" if latest_tepat > prev_tepat else "menurun" if latest_tepat < prev_tepat else "stabil"
                else:
                    tren_tepat = "tidak cukup data untuk tren"

                st.markdown("### Analisa Tren per-Bulan:")
                st.markdown(f"""
                - 📊 Rata-rata pelanggan tepat waktu: **{avg_tepat:.0f} ({persen_tepat:.2f}%)**
                - ⏰ Terlambat: **{avg_terlambat:.0f} ({persen_terlambat:.2f}%)**
                - 💸 Belum membayar: **{avg_belum_dibayar:.0f} ({persen_belum_dibayar:.2f}%)**
                - ✅ Tren pembayaran tepat waktu: **{tren_tepat}**
                """)
        else:
            st.warning(f"⚠️ Tidak ada data untuk bulan {selected_month}.")
