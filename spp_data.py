import streamlit as st
import pandas as pd
from datetime import datetime

# ====== PENGATURAN DASHBOARD ======
st.set_page_config(page_title="Dashboard SPP", layout="wide")
st.title("📊 Dashboard Rekap Pembayaran SPP")
st.markdown("Menampilkan status pembayaran siswa berdasarkan bulan dan kelas. Data otomatis diambil dari Google Form via Google Sheets.")

# ====== KONFIGURASI ======
JUMLAH_SPP = 1000000  # Nominal SPP per bulan
SHEET_ID = "1w_W1PATu-6_g4hXCK_2QzT6h7pl-ECAdpkxmdrVdoF8"  # Ganti dengan ID Google Sheets kamu
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/1w_W1PATu-6_g4hXCK_2QzT6h7pl-ECAdpkxmdrVdoF8/export?format=csv"

# ====== LOAD DATA GOOGLE SHEETS ======
@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)

    # Ambil 4 kolom terakhir (buang kolom Timestamp atau kolom tambahan)
    df = df.iloc[:, -4:]
    df.columns = ["Nama Siswa", "Kelas", "Tanggal Bayar", "Jumlah Bayar"]

    # Konversi tipe data
    df["Tanggal Bayar"] = pd.to_datetime(df["Tanggal Bayar"], errors="coerce")
    df["Jumlah Bayar"] = pd.to_numeric(df["Jumlah Bayar"], errors="coerce").fillna(0)

    # Tambahkan kolom bantu
    df["Bulan"] = df["Tanggal Bayar"].dt.month
    df["Tahun"] = df["Tanggal Bayar"].dt.year

    return df

try:
    data = load_data()
except Exception as e:
    st.error(f"Gagal memuat data dari Google Sheets: {e}")
    st.stop()

# ====== PILIH BULAN DAN TAHUN ======
bulan_dict = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

available_bulan = sorted(data["Bulan"].dropna().unique())
available_tahun = sorted(data["Tahun"].dropna().unique())

col1, col2 = st.columns(2)
bulan_pilih = col1.selectbox("📅 Pilih Bulan", available_bulan, format_func=lambda x: bulan_dict[int(x)])
tahun_pilih = col2.selectbox("📆 Pilih Tahun", available_tahun)

# ====== FILTER DATA SESUAI PILIHAN ======
data_filter = data[(data["Bulan"] == bulan_pilih) & (data["Tahun"] == tahun_pilih)]

# Ambil pembayaran sampai tanggal 10
sudah_bayar = data_filter[data_filter["Tanggal Bayar"].dt.day <= 10].copy()
semua_siswa = data[["Nama Siswa", "Kelas"]].drop_duplicates().copy()

# ====== PROSES REKAP ======
semua_siswa["Status"] = semua_siswa["Nama Siswa"].isin(sudah_bayar["Nama Siswa"])
semua_siswa["Status"] = semua_siswa["Status"].map({True: "Lunas", False: "Belum Lunas"})

total_bayar = sudah_bayar.groupby("Nama Siswa")["Jumlah Bayar"].sum().reset_index()
total_bayar.columns = ["Nama Siswa", "Total Bayar Bulan Ini"]

rekap = pd.merge(semua_siswa, total_bayar, on="Nama Siswa", how="left")
rekap["Total Bayar Bulan Ini"] = rekap["Total Bayar Bulan Ini"].fillna(0)
rekap["Kekurangan"] = JUMLAH_SPP - rekap["Total Bayar Bulan Ini"]
rekap["Kekurangan"] = rekap["Kekurangan"].clip(lower=0)
rekap = rekap.sort_values(by=["Kelas", "Nama Siswa"])

# ====== FILTER KELAS ======
kelas_pilih = st.selectbox("🏫 Filter Kelas", options=["Semua"] + sorted(rekap["Kelas"].dropna().unique()))

if kelas_pilih != "Semua":
    rekap = rekap[rekap["Kelas"] == kelas_pilih]

# ====== TAMPILKAN TABEL ======
st.subheader(f"📋 Rekap Bulan {bulan_dict[bulan_pilih]} {tahun_pilih}")
st.dataframe(rekap, use_container_width=True)

# ====== DOWNLOAD TOMBOL ======
csv = rekap.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Rekap CSV", data=csv, file_name="rekap_spp.csv", mime="text/csv")
