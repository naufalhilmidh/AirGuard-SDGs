"""Validasi prediksi kategori AirGuard dengan data aktual 22 Oktober 2026.

Skrip ini hanya mengambil satu hari dan tidak mengubah data mentah utama.
Jalankan dari root project:

    python src/data/validasi_prediksi_2026_10_22.py

Input:
    - data/data_gabungan/airguard_prediksi_besok.csv
    - data/kabkota_pulau_jawa.csv

Output:
    - data/data_gabungan/airguard_aktual_2026-10-22.csv
    - data/data_gabungan/validasi_prediksi_2026-10-22.csv
"""

from __future__ import annotations

import random
import time
from pathlib import Path

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
FILE_PREDIKSI = ROOT / "data" / "data_gabungan" / "airguard_prediksi_besok.csv"
DIR_OUTPUT = ROOT / "data" / "data_gabungan"

URL_UDARA = "https://air-quality-api.open-meteo.com/v1/air-quality"
TANGGAL_VALIDASI = "2026-10-22"
BATCH_SIZE = 10
MAX_RETRY = 5
BACKOFF_AWAL = 15
BACKOFF_MAKS = 300

KATEGORI = [
    "Baik (Aman)",
    "Sedang (Waspada)",
    "Tidak Sehat (Bahaya)",
]


def label_risiko(pm25: float) -> str:
    """Ambang harus sama dengan ambang saat membuat target model."""
    if pd.isna(pm25):
        return np.nan
    if pm25 <= 15:
        return KATEGORI[0]
    if pm25 <= 55:
        return KATEGORI[1]
    return KATEGORI[2]


def request_dengan_backoff(session: requests.Session, params: dict):
    """Request serial dengan exponential backoff dan jitter."""
    for percobaan in range(1, MAX_RETRY + 1):
        try:
            response = session.get(URL_UDARA, params=params, timeout=180)
        except requests.RequestException as error:
            if percobaan == MAX_RETRY:
                raise RuntimeError(f"Koneksi gagal setelah retry: {error}") from error
            tunggu = min(
                BACKOFF_MAKS,
                BACKOFF_AWAL * (2 ** (percobaan - 1)),
            ) + random.uniform(0, 5)
            print(f"   koneksi gagal; retry dalam {tunggu:.0f} detik")
            time.sleep(tunggu)
            continue

        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as error:
                raise RuntimeError("Respons API bukan JSON valid.") from error

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            try:
                tunggu_server = float(retry_after) if retry_after else 0
            except ValueError:
                tunggu_server = 0

            tunggu_backoff = min(
                BACKOFF_MAKS,
                BACKOFF_AWAL * (2 ** (percobaan - 1)),
            )
            tunggu = max(tunggu_server, tunggu_backoff) + random.uniform(0, 5)

            if percobaan == MAX_RETRY:
                raise RuntimeError("API tetap mengembalikan HTTP 429 setelah retry.")

            print(f"   HTTP 429; retry dalam {tunggu:.0f} detik")
            time.sleep(tunggu)
            continue

        raise RuntimeError(
            f"API mengembalikan HTTP {response.status_code}: "
            f"{response.text[:250]}"
        )

    raise RuntimeError("Request API gagal.")


def ambil_harian_satu_tanggal(kabkota: pd.DataFrame) -> pd.DataFrame:
    """Ambil hourly PM2.5 satu tanggal, lalu hitung rata-rata per wilayah."""
    hasil_semua = []

    with requests.Session() as session:
        for nomor, awal in enumerate(range(0, len(kabkota), BATCH_SIZE), start=1):
            batch = kabkota.iloc[awal:awal + BATCH_SIZE]
            print(f"Mengambil aktual {TANGGAL_VALIDASI} | batch {nomor} | "
                  f"{len(batch)} lokasi")

            params = {
                "latitude": ",".join(batch["latitude"].astype(str)),
                "longitude": ",".join(batch["longitude"].astype(str)),
                "hourly": "pm2_5",
                "start_date": TANGGAL_VALIDASI,
                "end_date": TANGGAL_VALIDASI,
                "timezone": "Asia/Jakarta",
                "domains": "cams_global",
            }
            response = request_dengan_backoff(session, params)
            lokasi = response if isinstance(response, list) else [response]

            if len(lokasi) != len(batch):
                raise RuntimeError(
                    f"Jumlah lokasi pada respons ({len(lokasi)}) tidak sama "
                    f"dengan batch ({len(batch)})."
                )

            for baris, data_lokasi in zip(batch.to_dict("records"), lokasi):
                hourly = data_lokasi.get("hourly", {})
                nilai = pd.to_numeric(
                    pd.Series(hourly.get("pm2_5", [])),
                    errors="coerce",
                )
                pm25 = nilai.mean()

                hasil_semua.append({
                    "kode_kabkota": str(baris["kode_kabkota"]),
                    "nama_kabkota": baris["nama_kabkota"],
                    "provinsi": baris["provinsi"],
                    "tanggal": TANGGAL_VALIDASI,
                    "pm2_5_aktual": pm25,
                    "jumlah_jam_tersedia": int(nilai.notna().sum()),
                })

            # Jeda kecil antar-request untuk mengurangi burst.
            time.sleep(3)

    aktual = pd.DataFrame(hasil_semua)
    aktual["kategori_aktual"] = aktual["pm2_5_aktual"].apply(label_risiko)
    return aktual


def validasi(aktual: pd.DataFrame, prediksi: pd.DataFrame) -> pd.DataFrame:
    prediksi = prediksi.copy()
    prediksi["kode_kabkota"] = prediksi["kode_kabkota"].astype(str)
    aktual["kode_kabkota"] = aktual["kode_kabkota"].astype(str)

    kolom_prediksi = [
        "kode_kabkota",
        "nama_kabkota",
        "provinsi",
        "tanggal_prediksi",
        "kategori_prediksi",
    ]
    gabung = aktual.merge(
        prediksi[kolom_prediksi],
        on=["kode_kabkota", "nama_kabkota", "provinsi"],
        how="left",
        validate="one_to_one",
    )

    gabung["benar"] = (
        gabung["kategori_aktual"] == gabung["kategori_prediksi"]
    )
    return gabung


def tampilkan_hasil(gabungan: pd.DataFrame):
    data = gabungan.dropna(subset=["kategori_aktual", "kategori_prediksi"]).copy()
    if data.empty:
        raise RuntimeError("Tidak ada baris yang bisa dibandingkan dengan prediksi.")

    y_aktual = data["kategori_aktual"]
    y_prediksi = data["kategori_prediksi"]
    akurasi = accuracy_score(y_aktual, y_prediksi)
    loss = 1 - akurasi

    print("\n=== HASIL VALIDASI PREDIKSI 22 OKTOBER 2026 ===")
    print(f"Wilayah berhasil dibandingkan: {len(data)}")
    print(f"Akurasi kategori            : {akurasi:.4f} ({akurasi * 100:.2f}%)")
    print(f"Classification loss/error   : {loss:.4f} ({loss * 100:.2f}%)")
    print(f"Balanced accuracy           : "
          f"{balanced_accuracy_score(y_aktual, y_prediksi):.4f}")
    print(f"Macro F1                    : "
          f"{f1_score(y_aktual, y_prediksi, average='macro'):.4f}")
    print("\nClassification report:")
    print(
        classification_report(
            y_aktual,
            y_prediksi,
            labels=KATEGORI,
            target_names=KATEGORI,
            zero_division=0,
            digits=4,
        )
    )
    print("Confusion matrix:")
    print(pd.DataFrame(
        confusion_matrix(y_aktual, y_prediksi, labels=KATEGORI),
        index=[f"Aktual: {x}" for x in KATEGORI],
        columns=[f"Prediksi: {x}" for x in KATEGORI],
    ))

    print("\nDistribusi aktual:")
    print(y_aktual.value_counts().reindex(KATEGORI, fill_value=0))
    print("\nDistribusi prediksi:")
    print(y_prediksi.value_counts().reindex(KATEGORI, fill_value=0))

    salah = data.loc[~data["benar"]].copy()
    if not salah.empty:
        print(f"\nJumlah prediksi salah: {len(salah)}")
        print(salah[
            ["nama_kabkota", "pm2_5_aktual", "kategori_aktual", "kategori_prediksi"]
        ].to_string(index=False))


def main():
    if not FILE_KABKOTA.exists():
        raise FileNotFoundError(f"File wilayah tidak ditemukan: {FILE_KABKOTA}")
    if not FILE_PREDIKSI.exists():
        raise FileNotFoundError(
            f"File prediksi tidak ditemukan: {FILE_PREDIKSI}. "
            "Jalankan uji_model_airguard.py --mode besok terlebih dahulu."
        )

    kabkota = pd.read_csv(
        FILE_KABKOTA,
        encoding="utf-8-sig",
        dtype={"kode_kabkota": "string"},
    )
    prediksi = pd.read_csv(FILE_PREDIKSI)

    aktual = ambil_harian_satu_tanggal(kabkota)
    file_aktual = DIR_OUTPUT / f"airguard_aktual_{TANGGAL_VALIDASI}.csv"
    aktual.to_csv(file_aktual, index=False)

    gabungan = validasi(aktual, prediksi)
    file_validasi = DIR_OUTPUT / f"validasi_prediksi_{TANGGAL_VALIDASI}.csv"
    gabungan.to_csv(file_validasi, index=False)

    print(f"\nData aktual tersimpan di : {file_aktual}")
    print(f"Hasil validasi tersimpan : {file_validasi}")
    tampilkan_hasil(gabungan)


if __name__ == "__main__":
    main()
