import streamlit as st
import pandas as pd
import requests
import plotly.express as px

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

def get_summary_thbl():
    try:
        response = requests.get("http://127.0.0.1:5000/get_summary_thbl", timeout=60)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Gagal mengambil data: {e}")
        return pd.DataFrame()

def fetch_data():
    try:
        response = requests.get("http://localhost:5000/get_late_subkelompok")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error("Gagal mengambil data")
            return pd.DataFrame()
    except:
        st.error("Error mengambil data dari server")
        return pd.DataFrame()

def get_zona():
    try:
        response = requests.get("http://localhost:5000/get_late_zona")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error("Gagal mengambil data zona")
            return pd.DataFrame()
    except:
        st.error("Error mengambil data zona")
        return pd.DataFrame()

def show():
    st.title("Dashboard Pola Pembayaran Pelanggan PDAM Surya Sembada")
    tab1, tab2 = st.tabs(["Pola Pembayaran per Bulan", "Pola Pembayaran per Kategori"])

    with tab1:
        from .pembayaran_perbulan import render_perbulan_tab
        render_perbulan_tab(get_summary, get_data, get_summary_thbl)

    with tab2:
        from .pembayaran_perkategori import render_perkategori_tab
        render_perkategori_tab(fetch_data, get_zona)
