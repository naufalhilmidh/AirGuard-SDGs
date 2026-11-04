"""Validasi prediksi kategori AirGuard pada 22-24 Oktober 2026.

Jalankan dari root project:

    python src/data/validasi_prediksi_2026_10_22_24.py

Skrip mengambil data aktual 22-24 Oktober, membuat prediksi berantai:
data tanggal 21 -> prediksi 22, data aktual 22 -> prediksi 23, dan data
aktual 23 -> prediksi 24. Hasil dan grafik disimpan di data_gabungan.
"""

from __future__ import annotations

import random
import time
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)


ROOT = Path(__file__).resolve().parents[2]
FILE_KABKOTA = ROOT / "data" / "kabkota_pulau_jawa.csv"
FILE_PREPROCESSED = ROOT / "data" / "data_gabungan" / "airguard_preprocessed.csv"
FILE_MODEL = ROOT / "models" / "airguard_model.joblib"
DIR_OUTPUT = ROOT / "data" / "data_gabungan"

URL_UDARA = "https://air-quality-api.open-meteo.com/v1/air-quality"
TANGGAL_AWAL = "2026-10-22"
TANGGAL_AKHIR = "2026-10-24"
BATCH_SIZE = 10
MAX_RETRY = 5
BACKOFF_AWAL = 15
BACKOFF_MAKS = 300

VARIABEL_UDARA = [
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
]
KATEGORI = ["Baik (Aman)", "Sedang (Waspada)", "Tidak Sehat (Bahaya)"]


def label_risiko(pm25):
    if pd.isna(pm25):
        return np.nan
    if pm25 <= 15:
        return KATEGORI[0]
    if pm25 <= 55:
        return KATEGORI[1]
    return KATEGORI[2]


def request_dengan_backoff(session, params):
    for percobaan in range(1, MAX_RETRY + 1):
        try:
            response = session.get(URL_UDARA, params=params, timeout=180)
        except requests.RequestException as error:
            if percobaan == MAX_RETRY:
                raise RuntimeError(f"Koneksi gagal setelah retry: {error}") from error
            tunggu = min(BACKOFF_MAKS, BACKOFF_AWAL * 2 ** (percobaan - 1))
            tunggu += random.uniform(0, 5)
            print(f"   koneksi gagal; retry dalam {tunggu:.0f} detik")
            time.sleep(tunggu)
            continue

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            try:
                tunggu_server = float(retry_after) if retry_after else 0
            except ValueError:
                tunggu_server = 0
            tunggu = max(
                tunggu_server,
                min(BACKOFF_MAKS, BACKOFF_AWAL * 2 ** (percobaan - 1)),
            ) + random.uniform(0, 5)
            if percobaan == MAX_RETRY:
                raise RuntimeError("API tetap mengembalikan HTTP 429 setelah retry.")
            print(f"   HTTP 429; retry dalam {tunggu:.0f} detik")
            time.sleep(tunggu)
            continue

        raise RuntimeError(
            f"API mengembalikan HTTP {response.status_code}: {response.text[:250]}"
        )

    raise RuntimeError("Request API gagal.")


def ambil_data_aktual(kabkota):
    """Mengambil semua polutan untuk 22-24 Oktober dan merata-ratakannya."""
    hasil_semua = []

    with requests.Session() as session:
        for nomor, awal in enumerate(range(0, len(kabkota), BATCH_SIZE), start=1):
            batch = kabkota.iloc[awal:awal + BATCH_SIZE]
            print(f"Mengambil aktual | {TANGGAL_AWAL} sampai {TANGGAL_AKHIR} | "
                  f"batch {nomor} | {len(batch)} lokasi")

            params = {
                "latitude": ",".join(batch["latitude"].astype(str)),
                "longitude": ",".join(batch["longitude"].astype(str)),
                "hourly": ",".join(VARIABEL_UDARA),
                "start_date": TANGGAL_AWAL,
                "end_date": TANGGAL_AKHIR,
                "timezone": "Asia/Jakarta",
                "domains": "cams_global",
            }
            response = request_dengan_backoff(session, params)
            lokasi = response if isinstance(response, list) else [response]
            if len(lokasi) != len(batch):
                raise RuntimeError("Jumlah lokasi pada respons API tidak sesuai batch.")

            for baris, data_lokasi in zip(batch.to_dict("records"), lokasi):
                hourly = pd.DataFrame(data_lokasi.get("hourly", {}))
                hourly["tanggal"] = pd.to_datetime(hourly["time"]).dt.date
                harian = hourly.groupby("tanggal", as_index=False)[VARIABEL_UDARA].mean()
                for kolom in ["kode_kabkota", "nama_kabkota", "provinsi"]:
                    harian[kolom] = baris[kolom]
                hasil_semua.append(harian)

            time.sleep(3)

    aktual = pd.concat(hasil_semua, ignore_index=True)
    aktual["tanggal"] = pd.to_datetime(aktual["tanggal"])
    aktual["kategori_aktual"] = aktual["pm2_5"].apply(label_risiko)
    aktual = aktual.rename(columns={"pm2_5": "pm2_5_aktual"})
    return aktual


def buat_fitur_untuk_prediksi(preprocessed, aktual, fitur_model):
    """Gabungkan histori dan aktual baru, lalu hitung fitur tanggal/lags/rolling."""
    kolom_dasar = [
        "kode_kabkota", "nama_kabkota", "provinsi", "tanggal",
        "latitude", "longitude", "elevasi_m", "luas_km2", "penduduk",
        *VARIABEL_UDARA,
    ]

    historis = preprocessed.copy()
    historis = historis.rename(columns={"pm2_5": "pm2_5"})
    historis = historis[kolom_dasar]

    tambahan = aktual.copy()
    tambahan = tambahan.rename(columns={"pm2_5_aktual": "pm2_5"})
    info = preprocessed[
        ["kode_kabkota", "latitude", "longitude", "elevasi_m", "luas_km2", "penduduk"]
    ].drop_duplicates("kode_kabkota")
    tambahan = tambahan.drop(columns=["kategori_aktual"], errors="ignore")
    tambahan = tambahan.merge(info, on="kode_kabkota", how="left")
    tambahan = tambahan[kolom_dasar]

    semua = pd.concat([historis, tambahan], ignore_index=True)
    semua["kode_kabkota"] = semua["kode_kabkota"].astype(str)
    semua = (
        semua.sort_values(["kode_kabkota", "tanggal"])
        .drop_duplicates(["kode_kabkota", "tanggal"], keep="last")
        .reset_index(drop=True)
    )

    grup = semua.groupby("kode_kabkota", sort=False)["pm2_5"]
    for lag in [1, 2, 3, 7, 14]:
        semua[f"pm2_5_lag_{lag}"] = grup.shift(lag)
    for window in [3, 7, 14]:
        semua[f"pm2_5_rolling_{window}"] = grup.transform(
            lambda nilai: nilai.rolling(window=window, min_periods=window).mean()
        )

    semua["tahun"] = semua["tanggal"].dt.year
    semua["bulan"] = semua["tanggal"].dt.month
    semua["hari_dalam_minggu"] = semua["tanggal"].dt.dayofweek
    semua["hari_dalam_tahun"] = semua["tanggal"].dt.dayofyear
    semua["akhir_pekan"] = (semua["hari_dalam_minggu"] >= 5).astype(int)

    hasil = semua[semua["tanggal"].isin(pd.to_datetime(["2026-10-21", "2026-10-22", "2026-10-23"]))].copy()
    hasil = hasil.dropna(subset=fitur_model)
    return hasil


def buat_prediksi_berantai(preprocessed, aktual, bundle):
    fitur_model = bundle["fitur"]
    model = bundle["model"]
    fitur = buat_fitur_untuk_prediksi(preprocessed, aktual, fitur_model)
    tanggal_input = pd.to_datetime(["2026-10-21", "2026-10-22", "2026-10-23"])
    fitur = fitur[fitur["tanggal"].isin(tanggal_input)].copy()
    fitur["tanggal_prediksi"] = fitur["tanggal"] + pd.Timedelta(days=1)

    pred = model.predict(fitur[fitur_model])
    label_balik = bundle.get("label_balik", {})
    fitur["kategori_prediksi"] = [label_balik.get(int(nilai), str(nilai)) for nilai in pred]
    fitur["kode_kabkota"] = fitur["kode_kabkota"].astype(str)

    aktual_ringkas = aktual[[
        "kode_kabkota", "tanggal", "pm2_5_aktual", "kategori_aktual"
    ]].rename(columns={"tanggal": "tanggal_prediksi"})
    hasil = fitur.merge(
        aktual_ringkas,
        on=["kode_kabkota", "tanggal_prediksi"],
        how="left",
        validate="one_to_one",
    )
    hasil["benar"] = hasil["kategori_aktual"] == hasil["kategori_prediksi"]
    return hasil[[
        "kode_kabkota", "nama_kabkota", "provinsi", "tanggal",
        "tanggal_prediksi", "pm2_5", "pm2_5_aktual",
        "kategori_prediksi", "kategori_aktual", "benar",
    ]].rename(columns={"tanggal": "tanggal_input", "pm2_5": "pm2_5_input"})


def buat_grafik(hasil, output):
    jumlah = (
        hasil.melt(
            id_vars="tanggal_prediksi",
            value_vars=["kategori_aktual", "kategori_prediksi"],
            var_name="jenis",
            value_name="kategori",
        )
        .groupby(["tanggal_prediksi", "jenis", "kategori"])
        .size()
        .reset_index(name="jumlah_wilayah")
    )
    nama_jenis = {"kategori_aktual": "Aktual", "kategori_prediksi": "Prediksi"}
    jumlah["jenis"] = jumlah["jenis"].map(nama_jenis)

    fig, ax = plt.subplots(figsize=(12, 6))
    warna = {KATEGORI[0]: "#4BAA78", KATEGORI[1]: "#C99A3E", KATEGORI[2]: "#B85C5C"}
    gaya = {"Aktual": "-o", "Prediksi": "--o"}
    for kategori in KATEGORI:
        for jenis in ["Aktual", "Prediksi"]:
            subset = jumlah[(jumlah["kategori"] == kategori) & (jumlah["jenis"] == jenis)]
            if not subset.empty:
                ax.plot(
                    subset["tanggal_prediksi"], subset["jumlah_wilayah"],
                    gaya[jenis], color=warna[kategori], label=f"{jenis} - {kategori}",
                )
    ax.set_title("Validasi Prediksi Kategori Risiko PM2.5\n22-24 Oktober 2026")
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Jumlah Kabupaten/Kota")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.show()
    plt.close(fig)


def main():
    for path in [FILE_KABKOTA, FILE_PREPROCESSED, FILE_MODEL]:
        if not path.exists():
            raise FileNotFoundError(f"File tidak ditemukan: {path}")

    kabkota = pd.read_csv(FILE_KABKOTA, encoding="utf-8-sig", dtype={"kode_kabkota": "string"})
    preprocessed = pd.read_csv(FILE_PREPROCESSED, parse_dates=["tanggal"])
    preprocessed["kode_kabkota"] = preprocessed["kode_kabkota"].astype(str)
    bundle = joblib.load(FILE_MODEL)

    aktual = ambil_data_aktual(kabkota)
    aktual_path = DIR_OUTPUT / "airguard_aktual_2026-10-22_24.csv"
    aktual.to_csv(aktual_path, index=False)

    hasil = buat_prediksi_berantai(preprocessed, aktual, bundle)
    hasil_path = DIR_OUTPUT / "validasi_prediksi_2026-10-22_24.csv"
    grafik_path = DIR_OUTPUT / "validasi_prediksi_2026-10-22_24.png"
    hasil.to_csv(hasil_path, index=False)

    data = hasil.dropna(subset=["kategori_aktual", "kategori_prediksi"])
    y_true = data["kategori_aktual"]
    y_pred = data["kategori_prediksi"]
    akurasi = accuracy_score(y_true, y_pred)

    print("\n=== VALIDASI 22-24 OKTOBER 2026 ===")
    print(f"Baris dibandingkan : {len(data)}")
    print(f"Akurasi kategori   : {akurasi:.4f} ({akurasi * 100:.2f}%)")
    print(f"Loss/error         : {(1 - akurasi):.4f} ({(1 - akurasi) * 100:.2f}%)")
    print(f"Balanced accuracy  : {balanced_accuracy_score(y_true, y_pred):.4f}")
    print(f"Macro F1           : {f1_score(y_true, y_pred, labels=KATEGORI, average='macro', zero_division=0):.4f}")
    print("\nClassification report:")
    print(classification_report(y_true, y_pred, labels=KATEGORI, target_names=KATEGORI, zero_division=0, digits=4))
    print("Confusion matrix:")
    print(pd.DataFrame(confusion_matrix(y_true, y_pred, labels=KATEGORI), index=KATEGORI, columns=KATEGORI))
    print(f"\nData aktual : {aktual_path}")
    print(f"Hasil CSV   : {hasil_path}")
    buat_grafik(hasil, grafik_path)
    print(f"Grafik      : {grafik_path}")


if __name__ == "__main__":
    main()
