import streamlit as st
from views import pembayaran_view, monitoring_view, indikasi_view

st.set_page_config(layout="wide")
st.sidebar.title("Menu")
st.sidebar.markdown("Selamat datang di aplikasi interaktif PDAM Surya Sembada")

nav_selection = st.sidebar.radio(
    "Pilih Menu",
    (
        "Dashboard Pola Pembayaran Pelanggan",
        "Layanan Monitoring Pelanggan",
        "Indikasi Pelanggan Terlambat"
    )
)

if nav_selection == "Dashboard Pola Pembayaran Pelanggan":
    pembayaran_view.show()

elif nav_selection == "Layanan Monitoring Pelanggan":
    monitoring_view.show()

elif nav_selection == "Indikasi Pelanggan Terlambat":
    indikasi_view.show()
