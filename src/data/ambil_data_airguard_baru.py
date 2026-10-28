# ============================================================
# AirGuard SDGs - Pengambilan Data Kualitas Udara & Cuaca
# Versi 2 : berdasarkan data kab/kota Pulau Jawa (kabkota_pulau_jawa.csv)
# Jobdesk : Data Collection (Naufal, Randi)
#
# Sumber data : Open-Meteo (gratis, tanpa API key)
#   - Kualitas udara : https://air-quality-api.open-meteo.com/v1/air-quality
#   - Cuaca historis : https://archive-api.open-meteo.com/v1/archive
#
# PENTING - batas pemakaian API gratis Open-Meteo:
#   10.000 panggilan/hari, 5.000/jam, 600/menit.
#   Satu request besar dihitung lebih dari 1 panggilan, rumusnya:
#       bobot = jumlah_lokasi * (jumlah_hari / 14) * (jumlah_variabel / 10)
#   Untuk 119 kab/kota dari 2022 sampai sekarang, totalnya sekitar
#   20.900 panggilan, jadi TIDAK cukup dalam 1 hari.
#   Karena itu program ini dibuat bisa BERHENTI dan DILANJUTKAN:
#   kab/kota yang sudah selesai disimpan, jadi tidak diunduh ulang.
#   Jalankan lagi program ini besok sampai semua kab/kota selesai.
#
# Output : data_mentah/     -> data per jam, 1 file per kab/kota per jenis
#          data_gabungan/   -> data harian semua kab/kota (1 file CSV)
# ============================================================

import os
import time
import json
import requests
import numpy as np
import pandas as pd
from datetime import date, timedelta

# ------------------------------------------------------------
# 1. PENGATURAN
# ------------------------------------------------------------

FILE_KABKOTA = "kabkota_pulau_jawa.csv"

# data kualitas udara Open-Meteo tersedia mulai 2022 (cek lagi di dokumentasi)
TAHUN_AWAL = 2022
# dikasih jeda 7 hari karena data arsip cuaca ada delay
TANGGAL_AKHIR = date.today() - timedelta(days=7)

# untuk uji coba isi angka (misal 3) supaya hanya 3 kab/kota yang diambil
# kalau mau semua kab/kota biarkan None
BATAS_KABKOTA = None

# variabel yang diambil
var_udara = "pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi"
var_cuaca = ("temperature_2m,relative_humidity_2m,precipitation,"
             "wind_speed_10m,wind_direction_10m,surface_pressure,cloud_cover")

URL_UDARA = "https://air-quality-api.open-meteo.com/v1/air-quality"
URL_CUACA = "https://archive-api.open-meteo.com/v1/archive"

# pengaturan kuota (batas resmi 10.000/hari dan 5.000/jam, kita sisakan margin)
BATAS_HARIAN = 9000
BATAS_PER_JAM = 4500
DETIK_PER_BOBOT = 3600 / BATAS_PER_JAM   # jeda antar request, makin besar bobot makin lama
FILE_LOG = "log_kuota.json"

# kolom informasi kab/kota yang ikut disimpan di data akhir
kolom_info = ["kode_kabkota", "nama_kabkota", "provinsi", "tipe",
              "latitude", "longitude", "elevasi_m", "luas_km2", "penduduk"]

# buat folder output kalau belum ada
os.makedirs("data_mentah", exist_ok=True)
os.makedirs("data_gabungan", exist_ok=True)

# penanda kalau server bilang kita sudah kena limit (status 429)
kena_limit = False


# ------------------------------------------------------------
# 2. FUNGSI BANTU KUOTA
# ------------------------------------------------------------

def baca_kuota():
    """Baca berapa kuota yang sudah terpakai HARI INI dari file log."""
    hari_ini = str(date.today())
    if os.path.exists(FILE_LOG):
        with open(FILE_LOG, "r") as f:
            data = json.load(f)
        if data.get("tanggal") == hari_ini:
            return data.get("terpakai", 0)
    return 0


def simpan_kuota(nilai):
    """Simpan kuota terpakai hari ini ke file log."""
    with open(FILE_LOG, "w") as f:
        json.dump({"tanggal": str(date.today()), "terpakai": nilai}, f)


def hitung_bobot(mulai, akhir, variabel):
    """Hitung bobot 1 request (1 lokasi) sesuai rumus Open-Meteo."""
    jumlah_hari = (akhir - mulai).days + 1
    jumlah_variabel = len(variabel.split(","))
    return (jumlah_hari / 14) * (jumlah_variabel / 10)


def buat_rentang_tahun():
    """Buat daftar (tanggal_mulai, tanggal_akhir) untuk tiap tahun."""
    daftar = []
    for tahun in range(TAHUN_AWAL, TANGGAL_AKHIR.year + 1):
        mulai = date(tahun, 1, 1)
        akhir = date(tahun, 12, 31)
        if akhir > TANGGAL_AKHIR:
            akhir = TANGGAL_AKHIR
        daftar.append((mulai, akhir))
    return daftar


def bobot_total(variabel):
    """Bobot untuk mengunduh 1 jenis data (udara/cuaca) 1 kab/kota, semua tahun."""
    total = 0
    for mulai, akhir in buat_rentang_tahun():
        total += hitung_bobot(mulai, akhir, variabel)
    return total


# ------------------------------------------------------------
# 3. FUNGSI PENGAMBIL DATA
# ------------------------------------------------------------

def ambil_json(url, params):
    """Kirim request ke API. Kalau gagal coba lagi sampai 3 kali."""
    global kena_limit
    for percobaan in range(3):
        try:
            respon = requests.get(url, params=params, timeout=60)
            if respon.status_code == 200:
                return respon.json()
            if respon.status_code == 429:
                # kena limit, tidak ada gunanya mencoba lagi
                print("   KENA LIMIT dari server (429). Berhenti dulu.")
                kena_limit = True
                return None
            if respon.status_code == 400:
                # parameter salah / tanggal di luar jangkauan, coba lagi pun hasilnya sama
                print("   Request ditolak (400):", respon.text[:200])
                return None
            print("   status", respon.status_code, "-> coba lagi")
        except Exception as e:
            print("   error:", e, "-> coba lagi")
        time.sleep(5)
    return None


def ambil_per_tahun(url, lat, lon, variabel, awalan):
    """Ambil data per tahun lalu gabungkan jadi satu DataFrame.
    Kalau ada 1 tahun yang gagal, hasilnya None (supaya tidak ada data bolong
    yang tersimpan, dan nanti bisa diulang)."""
    global terpakai
    semua = []
    for mulai, akhir in buat_rentang_tahun():
        bobot = hitung_bobot(mulai, akhir, variabel)

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": variabel,
            "start_date": mulai.strftime("%Y-%m-%d"),
            "end_date": akhir.strftime("%Y-%m-%d"),
            "timezone": "Asia/Jakarta",   # seluruh Pulau Jawa = WIB
        }
        hasil = ambil_json(url, params)
        if hasil is None or "hourly" not in hasil:
            print("   gagal ambil tahun", mulai.year)
            return None

        df = pd.DataFrame(hasil["hourly"])
        # titik grid model yang sebenarnya dipakai API (bisa beda dari koordinat kita)
        df["grid_lat_" + awalan] = hasil.get("latitude")
        df["grid_lon_" + awalan] = hasil.get("longitude")
        semua.append(df)

        # catat kuota yang terpakai
        terpakai = terpakai + bobot
        simpan_kuota(terpakai)

        # jeda supaya tidak melewati batas per jam
        time.sleep(bobot * DETIK_PER_BOBOT)

    return pd.concat(semua, ignore_index=True)


# ------------------------------------------------------------
# 4. TAHAP 1 : UNDUH DATA MENTAH PER KAB/KOTA
# ------------------------------------------------------------

# baca data kab/kota
# utf-8-sig supaya BOM di awal file tidak ikut jadi nama kolom
# kode_kabkota dibaca sebagai teks supaya "32.10" tidak berubah jadi "32.1"
kabkota = pd.read_csv(FILE_KABKOTA, encoding="utf-8-sig", dtype={"kode_kabkota": str})
# hapus spasi berlebih di awal/akhir teks (ada di beberapa nama kab/kota)
for kolom in ["provinsi", "nama_kabkota", "tipe"]:
    kabkota[kolom] = kabkota[kolom].str.strip()

if BATAS_KABKOTA is not None:
    kabkota = kabkota.head(BATAS_KABKOTA)

print("Jumlah kab/kota   :", len(kabkota))
print("Periode           :", TAHUN_AWAL, "sampai", TANGGAL_AKHIR)

terpakai = baca_kuota()
print("Kuota terpakai hari ini :", round(terpakai), "dari batas", BATAS_HARIAN)
print()

jenis_data = [
    ("udara", URL_UDARA, var_udara),
    ("cuaca", URL_CUACA, var_cuaca),
]

berhenti = False
for i, baris in kabkota.iterrows():
    kode = baris["kode_kabkota"].replace(".", "_")
    nama = baris["nama_kabkota"]

    for jenis, url, variabel in jenis_data:
        nama_file = "data_mentah/" + jenis + "_" + kode + ".csv"

        # kalau file sudah ada berarti sudah pernah diunduh, lewati
        if os.path.exists(nama_file):
            continue

        # cek apakah kuota hari ini masih cukup untuk 1 kab/kota ini
        kebutuhan = bobot_total(variabel)
        if terpakai + kebutuhan > BATAS_HARIAN:
            print("Kuota hari ini hampir habis. Berhenti di:", nama)
            print("Jalankan lagi program ini besok untuk melanjutkan.")
            berhenti = True
            break

        print("Mengambil", jenis, "-", nama, "(" + baris["kode_kabkota"] + ")")
        df = ambil_per_tahun(url, baris["latitude"], baris["longitude"], variabel, jenis)

        if df is None:
            print("   data", jenis, nama, "gagal, akan dicoba lagi di run berikutnya")
            if kena_limit:
                berhenti = True
                break
            continue

        df.to_csv(nama_file, index=False)

    if berhenti:
        break

print()
print("Kuota terpakai setelah run ini :", round(terpakai))


# ------------------------------------------------------------
# 5. TAHAP 2 : GABUNGKAN & UBAH KE HARIAN
#    (hanya kab/kota yang file udara DAN cuacanya sudah lengkap)
# ------------------------------------------------------------

daftar_harian = []
belum_selesai = []

for i, baris in kabkota.iterrows():
    kode = baris["kode_kabkota"].replace(".", "_")
    file_udara = "data_mentah/udara_" + kode + ".csv"
    file_cuaca = "data_mentah/cuaca_" + kode + ".csv"

    if not (os.path.exists(file_udara) and os.path.exists(file_cuaca)):
        belum_selesai.append(baris["nama_kabkota"])
        continue

    df_udara = pd.read_csv(file_udara)
    df_cuaca = pd.read_csv(file_cuaca)

    # gabungkan udara + cuaca berdasarkan kolom waktu
    df = pd.merge(df_udara, df_cuaca, on="time", how="inner")
    df["time"] = pd.to_datetime(df["time"])
    df["tanggal"] = df["time"].dt.date

    # arah angin tidak boleh dirata-rata biasa (rata-rata 350 derajat dan 10 derajat
    # bukan 180). Jadi diubah dulu ke sin dan cos, nanti dikembalikan ke derajat.
    df["wd_sin"] = np.sin(np.radians(df["wind_direction_10m"]))
    df["wd_cos"] = np.cos(np.radians(df["wind_direction_10m"]))

    # ubah dari per jam menjadi per hari
    # (curah hujan dijumlahkan, sisanya dirata-rata)
    kolom_angka = [c for c in df.columns if c not in ["time", "tanggal"]]
    aturan = {c: "mean" for c in kolom_angka}
    aturan["precipitation"] = lambda x: x.sum(min_count=1)
    harian = df.groupby("tanggal").agg(aturan).reset_index()

    # kembalikan arah angin ke satuan derajat 0-360
    harian["wind_direction_10m"] = np.degrees(
        np.arctan2(harian["wd_sin"], harian["wd_cos"])) % 360
    harian = harian.drop(columns=["wd_sin", "wd_cos"])

    # tambahkan kolom informasi kab/kota di bagian depan
    for urutan, kolom in enumerate(kolom_info):
        harian.insert(urutan, kolom, baris[kolom])

    daftar_harian.append(harian)


# ------------------------------------------------------------
# 6. SIMPAN HASIL AKHIR
# ------------------------------------------------------------

print()
print("Kab/kota selesai       :", len(daftar_harian), "dari", len(kabkota))
if len(belum_selesai) > 0:
    print("Kab/kota belum selesai :", len(belum_selesai))

if len(daftar_harian) > 0:
    data_akhir = pd.concat(daftar_harian, ignore_index=True)
    data_akhir.to_csv("data_gabungan/airguard_harian_kabkota_jawa.csv", index=False)

    titik_grid = data_akhir[["grid_lat_udara", "grid_lon_udara"]].drop_duplicates()
    print("Total baris            :", len(data_akhir))
    print("Titik grid udara unik  :", len(titik_grid))
    print("Missing value per kolom:")
    print(data_akhir.isnull().sum())
    print("Tersimpan di data_gabungan/airguard_harian_kabkota_jawa.csv")
else:
    print("Belum ada kab/kota yang lengkap datanya.")