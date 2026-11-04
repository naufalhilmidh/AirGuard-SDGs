"""Validasi model pada satu kabupaten/kota sepanjang periode data.

Contoh penggunaan dari root project:

    python src/data/validasi_satu_kota.py
    python src/data/validasi_satu_kota.py --kota "Kota Administrasi Jakarta Selatan"

Model yang digunakan adalah model klasifikasi, sehingga grafik utama
membandingkan kategori aktual dan kategori prediksi dengan kode:
0 = Baik, 1 = Sedang, 2 = Tidak Sehat.
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
)
from sklearn.exceptions import InconsistentVersionWarning


# Peringatan ini berasal dari perbedaan versi scikit-learn saat model disimpan
# dan saat model dibaca. Tidak perlu memenuhi output evaluasi utama.
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)


ROOT = Path(__file__).resolve().parents[2]
FILE_DATA = ROOT / "data" / "data_gabungan" / "airguard_preprocessed.csv"
FILE_MODEL = ROOT / "models" / "airguard_model.joblib"
FILE_VALIDASI_LANJUT = ROOT / "data" / "data_gabungan" / "validasi_prediksi_2026-10-22_24.csv"
DIR_OUTPUT = ROOT / "data" / "data_gabungan"

KATEGORI = ["Baik (Aman)", "Sedang (Waspada)", "Tidak Sehat (Bahaya)"]
KODE_KATEGORI = {nama: nomor for nomor, nama in enumerate(KATEGORI)}


def muat_data():
    df = pd.read_csv(FILE_DATA, parse_dates=["tanggal"])
    df["tahun"] = df["tanggal"].dt.year
    df["bulan"] = df["tanggal"].dt.month
    df["hari_dalam_minggu"] = df["tanggal"].dt.dayofweek
    df["hari_dalam_tahun"] = df["tanggal"].dt.dayofyear
    df["akhir_pekan"] = (df["hari_dalam_minggu"] >= 5).astype(int)
    return df.sort_values(["nama_kabkota", "tanggal"]).reset_index(drop=True)


def pilih_kota(df, nama_kota=None):
    if nama_kota:
        pilihan = df[df["nama_kabkota"].str.casefold() == nama_kota.casefold()].copy()
        if pilihan.empty:
            cocok = df[
                df["nama_kabkota"].str.contains(nama_kota, case=False, na=False)
            ]
            if cocok.empty:
                daftar = sorted(df["nama_kabkota"].unique())
                raise ValueError(
                    f"Kota '{nama_kota}' tidak ditemukan. Contoh nama yang tersedia: {daftar[:10]}"
                )
            pilihan = cocok.copy()
        return pilihan, pilihan["nama_kabkota"].iloc[0]

    # Default: wilayah dengan rata-rata PM2.5 tertinggi.
    ringkasan = df.groupby("nama_kabkota")["pm2_5"].mean().sort_values(ascending=False)
    nama_tertinggi = ringkasan.index[0]
    return df[df["nama_kabkota"] == nama_tertinggi].copy(), nama_tertinggi


def tambahkan_validasi_terbaru(data, nama_kota):
    """Menambahkan hasil validasi 22-24 Oktober jika file tersebut tersedia."""
    if not FILE_VALIDASI_LANJUT.exists():
        print(
            f"Catatan: {FILE_VALIDASI_LANJUT.name} belum ada. "
            "Grafik berakhir pada tanggal terakhir data preprocessing."
        )
        return data

    lanjut = pd.read_csv(FILE_VALIDASI_LANJUT, parse_dates=["tanggal_prediksi"])
    lanjut = lanjut[
        lanjut["nama_kabkota"].str.casefold() == nama_kota.casefold()
    ].copy()
    if lanjut.empty:
        return data

    tambahan = pd.DataFrame({
        "kode_kabkota": lanjut["kode_kabkota"],
        "nama_kabkota": lanjut["nama_kabkota"],
        "provinsi": lanjut["provinsi"],
        "tanggal": lanjut["tanggal_prediksi"],
        "tanggal_grafik": lanjut["tanggal_prediksi"],
        "pm2_5": lanjut["pm2_5_input"],
        "pm2_5_target_aktual": lanjut["pm2_5_aktual"],
        "kategori_target_pm2_5": lanjut["kategori_aktual"],
        "kategori_prediksi": lanjut["kategori_prediksi"],
    })
    tambahan["kode_aktual"] = tambahan["kategori_target_pm2_5"].map(KODE_KATEGORI)
    tambahan["kode_prediksi"] = tambahan["kategori_prediksi"].map(KODE_KATEGORI)
    tambahan["benar"] = (
        tambahan["kategori_target_pm2_5"] == tambahan["kategori_prediksi"]
    )

    data = pd.concat([data, tambahan], ignore_index=True)
    data = (
        data.sort_values("tanggal_grafik")
        .drop_duplicates("tanggal_grafik", keep="last")
        .reset_index(drop=True)
    )
    print("Validasi terbaru ditambahkan sampai:", data["tanggal_grafik"].max().date())
    return data


def main():
    parser = argparse.ArgumentParser(description="Validasi model pada satu kota.")
    parser.add_argument(
        "--kota",
        default="Kota Administrasi Jakarta Selatan",
        help="Nama kabupaten/kota; default Jakarta Selatan.",
    )
    args = parser.parse_args()

    if not FILE_DATA.exists():
        raise FileNotFoundError(f"Data tidak ditemukan: {FILE_DATA}")
    if not FILE_MODEL.exists():
        raise FileNotFoundError(f"Model tidak ditemukan: {FILE_MODEL}")

    df = muat_data()
    bundle = joblib.load(FILE_MODEL)
    model = bundle["model"]
    fitur = bundle["fitur"]
    label_balik = bundle.get("label_balik", {})

    data, nama_kota = pilih_kota(df, args.kota)
    data = data.dropna(subset=fitur + ["kategori_target_pm2_5"]).copy()
    if data.empty:
        raise ValueError(f"Tidak ada data lengkap untuk {nama_kota}.")

    y_true = data["kategori_target_pm2_5"]
    y_pred_encoded = model.predict(data[fitur])
    y_pred = pd.Series(
        [label_balik.get(int(nilai), str(nilai)) for nilai in y_pred_encoded],
        index=data.index,
    )

    data["kategori_prediksi"] = y_pred
    data["kode_aktual"] = data["kategori_target_pm2_5"].map(KODE_KATEGORI)
    data["kode_prediksi"] = data["kategori_prediksi"].map(KODE_KATEGORI)
    data["pm2_5_target_aktual"] = data["target_pm2_5"]
    data["benar"] = data["kategori_target_pm2_5"] == data["kategori_prediksi"]
    data["tanggal_grafik"] = data["tanggal"] + pd.Timedelta(days=1)

    # Tambahkan hasil validasi aktual 22-24 Oktober 2026 jika sudah dibuat.
    # Dengan demikian ujung grafik dapat mencapai 24 Oktober 2026.
    data = tambahkan_validasi_terbaru(data, nama_kota)

    # Validasi yang benar hanya memakai data aktual hasil crawling terbaru,
    # bukan seluruh histori. Untuk satu kota, periode 22-24 berarti maksimal
    # tiga observasi harian.
    tanggal_validasi = pd.to_datetime([
        "2026-10-22", "2026-10-23", "2026-10-24"
    ])
    data_uji = data[data["tanggal_grafik"].isin(tanggal_validasi)].copy()
    if data_uji.empty:
        raise ValueError(
            "Data validasi 22-24 Oktober 2026 belum tersedia. "
            "Jalankan crawler validasi terlebih dahulu."
        )

    y_true = data_uji["kategori_target_pm2_5"]
    y_pred = data_uji["kategori_prediksi"]

    akurasi = accuracy_score(y_true, y_pred)
    loss = 1 - akurasi
    print(f"=== VALIDASI SATU WILAYAH: {nama_kota} ===")
    print(f"Periode validasi   : {data_uji['tanggal_grafik'].min():%Y-%m-%d} sampai {data_uji['tanggal_grafik'].max():%Y-%m-%d}")
    print(f"Jumlah hari diuji  : {len(data_uji)}")
    print(f"Akurasi kategori   : {akurasi:.4f} ({akurasi * 100:.2f}%)")
    print(f"Classification loss: {loss:.4f} ({loss * 100:.2f}%)")

    nama_file = "".join(char if char.isalnum() else "_" for char in nama_kota).strip("_")
    file_csv = DIR_OUTPUT / f"validasi_{nama_file}.csv"
    file_png = DIR_OUTPUT / f"validasi_{nama_file}.png"
    file_png_kategori = DIR_OUTPUT / f"validasi_{nama_file}_garis_kategori.png"
    data[[
        "kode_kabkota", "nama_kabkota", "provinsi", "tanggal",
        "pm2_5", "pm2_5_target_aktual", "kategori_target_pm2_5",
        "kategori_prediksi", "benar",
    ]].to_csv(file_csv, index=False)

    # Grafik khusus agar garis prediksi kategori terlihat jelas.
    fig_kategori, ax_kategori = plt.subplots(figsize=(15, 6))
    ax_kategori.step(
        data["tanggal_grafik"], data["kode_aktual"], where="mid",
        color="#222222", linewidth=1.4, label="Aktual",
    )
    ax_kategori.step(
        data["tanggal_grafik"], data["kode_prediksi"], where="mid",
        color="#E67E22", linestyle="--", linewidth=1.4,
        label="Prediksi model",
    )
    ax_kategori.set_yticks(range(3), ["Baik", "Sedang", "Tidak Sehat"])
    ax_kategori.set_xlabel("Tanggal target")
    ax_kategori.set_ylabel("Kategori risiko PM2.5")
    ax_kategori.set_title(f"Garis Aktual vs Prediksi Kategori Risiko PM2.5\n{nama_kota}")
    ax_kategori.grid(alpha=0.3)
    ax_kategori.legend()
    fig_kategori.autofmt_xdate()
    fig_kategori.tight_layout()
    fig_kategori.savefig(file_png_kategori, dpi=160)
    plt.close(fig_kategori)

    # Grafik 1: garis kategori aktual vs prediksi sepanjang waktu.
    fig, axes = plt.subplots(2, 1, figsize=(15, 9), sharex=True)
    axes[0].step(
        data["tanggal_grafik"], data["kode_aktual"], where="mid",
        color="#333333", linewidth=1.2, label="Kategori aktual",
    )
    axes[0].step(
        data["tanggal_grafik"], data["kode_prediksi"], where="mid",
        color="#C0392B", alpha=0.8, linewidth=1.0, label="Kategori prediksi",
    )
    axes[0].set_yticks(range(3), ["Baik", "Sedang", "Tidak Sehat"])
    axes[0].set_ylabel("Kategori risiko")
    axes[0].set_title(f"Aktual vs Prediksi Kategori Risiko PM2.5\n{nama_kota}")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    # Grafik 2: PM2.5 aktual beserta ambang kategori.
    axes[1].plot(
        data["tanggal_grafik"], data["pm2_5_target_aktual"],
        color="#8E1B1B", linewidth=1.1, label="PM2.5 aktual hari berikutnya",
    )
    axes[1].axhline(15, color="#4BAA78", linestyle="--", label="Ambang Baik: 15")
    axes[1].axhline(55, color="#C0392B", linestyle="--", label="Ambang Tidak Sehat: 55")
    axes[1].set_ylabel("PM2.5 (µg/m³)")
    axes[1].set_xlabel("Tanggal input")
    axes[1].set_title("Nilai PM2.5 Aktual sebagai Dasar Kategori Risiko")
    axes[1].grid(alpha=0.3)
    axes[1].legend()

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(file_png, dpi=160)
    plt.show()
    plt.close(fig)

    print(f"\nData validasi tersimpan: {file_csv}")
    print(f"Grafik tersimpan       : {file_png}")
    print(f"Grafik kategori        : {file_png_kategori}")


if __name__ == "__main__":
    main()
