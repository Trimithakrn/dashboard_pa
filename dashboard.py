# app.py

import streamlit as st
from streamlit_option_menu import option_menu
from views import pembayaran_view, monitoring_view, indikasi_view, tambah_view


# Streamlit page config
st.set_page_config(page_title="PDAM Dashboard", layout="wide")

# Sidebar navigation menu
with st.sidebar:
    st.markdown("## Analisis Tagihan Pembayaran PDAM Surya Sembada")
    selected = option_menu(
        menu_title="Menu",
        options=[
            "Dashboard Pola Pembayaran Pelanggan",
            "Layanan Monitoring Pelanggan",
            "Pelanggan Belum Membayar Tagihan",
            "Tambahkan Data"  # <<<-- TAMBAHAN: Opsi baru
        ],
        icons=[
            "bar-chart",
            "list-task",
            "exclamation-triangle",
            "plus-circle"  # <<<-- TAMBAHAN: Ikon untuk opsi baru
        ],
        menu_icon="water",
        default_index=0,
        styles={
            "icon": {"color": "black", "font-size": "18px"},
            "nav-link": {
                "color": "black",
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
            },
            "nav-link-selected": {
                "background-color": "#FD706E",
                "color": "white"
            },
        }
    )

# Page content rendering
def show_pembayaran_view():
    st.title("📊 Dashboard Pola Pembayaran Pelanggan")
    pembayaran_view.show()

def show_monitoring_view():
    st.title("📋 Layanan Monitoring Pelanggan")
    monitoring_view.show()

def show_indikasi_view():
    st.title("🚨 Pelanggan Belum Membayar Tagihan")
    indikasi_view.show()

def show_tambah_view():
    st.title("➕ Tambahkan Data")
    tambah_view.show()

# Routing based on selection
if selected == "Dashboard Pola Pembayaran Pelanggan":
    show_pembayaran_view()

elif selected == "Layanan Monitoring Pelanggan":
    show_monitoring_view()

elif selected == "Pelanggan Belum Membayar Tagihan":
    show_indikasi_view()

elif selected == "Tambahkan Data": 
    show_tambah_view()