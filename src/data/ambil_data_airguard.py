# ============================================================
# AirGuard SDGs - Pengambilan Data Kualitas Udara & Cuaca
# Jobdesk: Data Collection (Naufal, Randi)
#
# Sumber data : Open-Meteo (gratis, tanpa API key)
#   - Kualitas udara : https://air-quality-api.open-meteo.com/v1/air-quality
#   - Cuaca historis : https://archive-api.open-meteo.com/v1/archive
# Output      : folder data_mentah/ dan data_gabungan/
# ============================================================

import os
import time
import requests
import pandas as pd
from datetime import date, timedelta

# ------------------------------------------------------------
# 1. PENGATURAN
# ------------------------------------------------------------

# daftar kota beserta koordinatnya (latitude, longitude)
kota = {
    "Jakarta":    (-6.2088, 106.8456),
    "Surabaya":   (-7.2575, 112.7521),
    "Bandung":    (-6.9175, 107.6191),
    "Medan":      (3.5952, 98.6722),
    "Semarang":   (-6.9667, 110.4167),
    "Makassar":   (-5.1477, 119.4327),
    "Palembang":  (-2.9761, 104.7754),
    "Yogyakarta": (-7.7956, 110.3695),
    "Pontianak":  (-0.0263, 109.3425),
    "Banjarmasin": (-3.3186, 114.5944),
}

# rentang tanggal
# data kualitas udara Open-Meteo tersedia mulai 2022-01-01
tahun_awal = 2022
tanggal_akhir = date.today() - timedelta(days=7)  # dikasih jeda 7 hari, data arsip cuaca ada delay

# variabel yang diambil
var_udara = "pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi"
var_cuaca = ("temperature_2m,relative_humidity_2m,precipitation,"
             "wind_speed_10m,wind_direction_10m,surface_pressure,cloud_cover")

URL_UDARA = "https://air-quality-api.open-meteo.com/v1/air-quality"
URL_CUACA = "https://archive-api.open-meteo.com/v1/archive"

# buat folder output kalau belum ada
os.makedirs("data_mentah", exist_ok=True)
os.makedirs("data_gabungan", exist_ok=True)


# ------------------------------------------------------------
# 2. FUNGSI PENGAMBIL DATA
# ------------------------------------------------------------

def ambil_json(url, params):
    """Kirim request ke API, kalau gagal coba lagi sampai 3 kali."""
    for percobaan in range(3):
        try:
            respon = requests.get(url, params=params, timeout=60)
            if respon.status_code == 200:
                return respon.json()
            print("   status", respon.status_code, "-> coba lagi")
        except Exception as e:
            print("   error:", e, "-> coba lagi")
        time.sleep(5)
    return None


def ambil_per_tahun(url, lat, lon, variabel, nama_kota):
    """Ambil data per tahun (supaya tidak kena batas ukuran request),
    lalu gabungkan semua tahun jadi satu DataFrame."""
    semua = []
    for tahun in range(tahun_awal, tanggal_akhir.year + 1):
        mulai = date(tahun, 1, 1)
        akhir = date(tahun, 12, 31)
        if akhir > tanggal_akhir:
            akhir = tanggal_akhir

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": variabel,
            "start_date": mulai.strftime("%Y-%m-%d"),
            "end_date": akhir.strftime("%Y-%m-%d"),
            "timezone": "Asia/Jakarta",
        }
        hasil = ambil_json(url, params)
        if hasil is None or "hourly" not in hasil:
            print("   gagal ambil", nama_kota, tahun)
            continue

        df = pd.DataFrame(hasil["hourly"])
        semua.append(df)
        time.sleep(1)  # jeda biar tidak kena limit

    if len(semua) == 0:
        return None
    return pd.concat(semua, ignore_index=True)


# ------------------------------------------------------------
# 3. LOOP SEMUA KOTA
# ------------------------------------------------------------

daftar_harian = []

for nama, (lat, lon) in kota.items():
    print("Mengambil data:", nama)

    # --- kualitas udara ---
    df_udara = ambil_per_tahun(URL_UDARA, lat, lon, var_udara, nama)
    # --- cuaca ---
    df_cuaca = ambil_per_tahun(URL_CUACA, lat, lon, var_cuaca, nama)

    if df_udara is None or df_cuaca is None:
        print("   data", nama, "tidak lengkap, dilewati")
        continue

    # simpan data mentah per jam
    df_udara.to_csv("data_mentah/udara_" + nama + ".csv", index=False)
    df_cuaca.to_csv("data_mentah/cuaca_" + nama + ".csv", index=False)

    # gabungkan udara + cuaca berdasarkan kolom waktu
    df = pd.merge(df_udara, df_cuaca, on="time", how="inner")
    df["time"] = pd.to_datetime(df["time"])
    df["tanggal"] = df["time"].dt.date

    # ubah dari per jam menjadi rata-rata per hari
    # (curah hujan dijumlahkan, sisanya dirata-rata)
    kolom_angka = [c for c in df.columns if c not in ["time", "tanggal"]]
    aturan = {c: "mean" for c in kolom_angka}
    aturan["precipitation"] = "sum"
    harian = df.groupby("tanggal").agg(aturan).reset_index()

    harian.insert(0, "kota", nama)
    harian.insert(1, "latitude", lat)
    harian.insert(2, "longitude", lon)
    daftar_harian.append(harian)

    print("   selesai,", len(harian), "hari")


# ------------------------------------------------------------
# 4. GABUNGKAN SEMUA KOTA & SIMPAN
# ------------------------------------------------------------

if len(daftar_harian) > 0:
    data_akhir = pd.concat(daftar_harian, ignore_index=True)
    data_akhir.to_csv("data_gabungan/airguard_harian_semua_kota.csv", index=False)
    print()
    print("Total baris :", len(data_akhir))
    print("Jumlah kota :", data_akhir["kota"].nunique())
    print("Missing value per kolom:")
    print(data_akhir.isnull().sum())
    print("Tersimpan di data_gabungan/airguard_harian_semua_kota.csv")
else:
    print("Tidak ada data yang berhasil diambil. Cek koneksi internet.")
