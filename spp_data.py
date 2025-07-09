import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Rekap SPP Bulanan", layout="wide")

st.title("📊 Rekap Pembayaran SPP Bulanan")
st.write("Dashboard ini menunjukkan status pembayaran SPP siswa sampai tanggal 10 setiap bulannya.")

# ===================== #
# CONFIG
# ===================== #
JUMLAH_SPP = 1000000  # Ubah sesuai kebutuhan
TANGGAL_REKAP = datetime.today().replace(day=10)

# ===================== #
# LOAD DATA
# ===================== #
try:
    data = pd.read_csv("spp_data.csv", skiprows=4, header=0)
    data.columns = ['Nama Siswa', 'Kelas', 'Tanggal Bayar', 'Jumlah Bayar']

    data['Tanggal Bayar'] = pd.to_datetime(data['Tanggal Bayar'], format='%d/%m/%Y', errors='coerce')
    data['Jumlah Bayar'] = (
        data['Jumlah Bayar'].astype(str)
        .str.replace('Rp', '', regex=False)
        .str.replace('.', '', regex=False)
    )
    data['Jumlah Bayar'] = pd.to_numeric(data['Jumlah Bayar'], errors='coerce').fillna(0)

except Exception as e:
    st.error(f"Gagal membaca file data: {e}")
    st.stop()

# ===================== #
# FILTER DAN REKAP
# ===================== #
data["Bulan"] = data["Tanggal Bayar"].dt.month
data["Tahun"] = data["Tanggal Bayar"].dt.year

bulan_ini = TANGGAL_REKAP.month
tahun_ini = TANGGAL_REKAP.year

sudah_bayar = data[
    (data["Bulan"] == bulan_ini) &
    (data["Tahun"] == tahun_ini) &
    (data["Tanggal Bayar"] <= TANGGAL_REKAP)
].copy()

semua_siswa = data[["Nama Siswa", "Kelas"]].drop_duplicates().copy()
semua_siswa["Status"] = semua_siswa["Nama Siswa"].isin(sudah_bayar["Nama Siswa"])
semua_siswa["Status"] = semua_siswa["Status"].map({True: "Lunas", False: "Belum Lunas"})

total_bayar = sudah_bayar.groupby("Nama Siswa")["Jumlah Bayar"].sum().reset_index()
total_bayar.columns = ["Nama Siswa", "Total Bayar Bulan Ini"]

rekap = pd.merge(semua_siswa, total_bayar, on="Nama Siswa", how="left")
rekap["Total Bayar Bulan Ini"] = rekap["Total Bayar Bulan Ini"].fillna(0)
rekap["Kekurangan"] = JUMLAH_SPP - rekap["Total Bayar Bulan Ini"]
rekap["Kekurangan"] = rekap["Kekurangan"].clip(lower=0)

rekap = rekap.sort_values(by=["Kelas", "Nama Siswa"])

# ===================== #
# STREAMLIT DISPLAY
# ===================== #
kelas_terpilih = st.selectbox("Pilih Kelas", options=["Semua"] + sorted(rekap["Kelas"].unique()))

if kelas_terpilih != "Semua":
    rekap = rekap[rekap["Kelas"] == kelas_terpilih]

st.dataframe(rekap, use_container_width=True)

# Unduh hasil
st.download_button("⬇️ Download Rekap ke CSV", data=rekap.to_csv(index=False), file_name="rekap_spp.csv", mime="text/csv")
