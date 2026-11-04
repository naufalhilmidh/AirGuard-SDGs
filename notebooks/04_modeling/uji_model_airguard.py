"""Uji model klasifikasi AirGuard pada data test atau data terbaru.

Jalankan dari root project:

    python notebooks/04_modeling/uji_model_airguard.py --mode besok
    python notebooks/04_modeling/uji_model_airguard.py --mode test
    python notebooks/04_modeling/uji_model_airguard.py --mode keduanya

Mode besok memakai satu baris terbaru dari setiap kabupaten/kota. Karena
fitur lag dan rolling sudah dibuat pada tahap preprocessing, skrip tidak
menghitung ulang fitur tersebut dan tidak memakai target sebagai fitur.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "airguard_model.joblib"
DATA_PATH = ROOT / "data" / "data_gabungan" / "airguard_preprocessed.csv"
OUTPUT_DIR = ROOT / "data" / "data_gabungan"

# Periode ini mengikuti pembagian waktu yang dipakai saat pemodelan.
TEST_START = pd.Timestamp("2026-01-01")


def baca_bundle():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model tidak ditemukan: {MODEL_PATH}")

    try:
        bundle = joblib.load(MODEL_PATH)
    except ModuleNotFoundError as exc:
        if exc.name == "lightgbm":
            raise RuntimeError(
                "LightGBM belum terpasang pada environment ini. "
                "Pasang dengan: python -m pip install lightgbm"
            ) from exc
        raise

    if not isinstance(bundle, dict) or "model" not in bundle or "fitur" not in bundle:
        raise ValueError(
            "Format airguard_model.joblib tidak sesuai. "
            "Model harus disimpan sebagai bundle dengan kunci 'model' dan 'fitur'."
        )

    return bundle


def baca_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data preprocessing tidak ditemukan: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, parse_dates=["tanggal"])
    df = df.sort_values(["kode_kabkota", "tanggal"]).reset_index(drop=True)

    # Fitur kalender harus sama dengan yang digunakan saat training.
    df["tahun"] = df["tanggal"].dt.year
    df["bulan"] = df["tanggal"].dt.month
    df["hari_dalam_minggu"] = df["tanggal"].dt.dayofweek
    df["hari_dalam_tahun"] = df["tanggal"].dt.dayofyear
    df["akhir_pekan"] = (df["hari_dalam_minggu"] >= 5).astype(int)
    return df


def siapkan_fitur(df: pd.DataFrame, fitur: list[str]) -> pd.DataFrame:
    tidak_ada = [kolom for kolom in fitur if kolom not in df.columns]
    if tidak_ada:
        raise KeyError(
            "Fitur yang diperlukan model belum tersedia: " + ", ".join(tidak_ada)
        )

    X = df[fitur].copy()
    if X.isna().any().any():
        detail = X.isna().sum()
        detail = detail[detail > 0].to_dict()
        raise ValueError(f"Masih ada missing value pada fitur model: {detail}")
    return X


def nama_label(bundle, nilai):
    label_balik = bundle.get("label_balik", {})
    # Key pada pickle bisa berupa int Python atau np.int64.
    try:
        return label_balik[int(nilai)]
    except (KeyError, TypeError, ValueError):
        return str(nilai)


def tambah_probabilitas(hasil: pd.DataFrame, proba: np.ndarray, bundle):
    model = bundle["model"]
    classes = getattr(model, "classes_", range(proba.shape[1]))
    for posisi, kelas in enumerate(classes):
        hasil[f"proba_{nama_label(bundle, kelas)}"] = proba[:, posisi]
    return hasil


def prediksi_besok(df: pd.DataFrame, bundle):
    """Prediksi H+1 memakai observasi terbaru masing-masing wilayah."""
    fitur = bundle["fitur"]
    model = bundle["model"]

    terbaru = (
        df.sort_values(["kode_kabkota", "tanggal"])
        .groupby("kode_kabkota", as_index=False, sort=False)
        .tail(1)
        .copy()
    )

    tanggal_terbaru = terbaru["tanggal"].max()
    tanggal_per_wilayah = terbaru.groupby("kode_kabkota")["tanggal"].nunique()
    if len(tanggal_per_wilayah) > 1:
        print("Peringatan: tanggal terakhir tidak sama untuk semua wilayah.")

    X = siapkan_fitur(terbaru, fitur)
    prediksi = model.predict(X)
    proba = model.predict_proba(X)

    hasil = terbaru[
        ["kode_kabkota", "nama_kabkota", "provinsi", "tanggal", "pm2_5"]
    ].rename(
        columns={
            "tanggal": "tanggal_input",
            "pm2_5": "pm2_5_hari_ini",
        }
    )
    hasil["tanggal_prediksi"] = hasil["tanggal_input"] + pd.Timedelta(days=1)
    hasil["kategori_prediksi"] = [nama_label(bundle, nilai) for nilai in prediksi]
    hasil = tambah_probabilitas(hasil, proba, bundle)
    hasil = hasil.sort_values("kategori_prediksi").reset_index(drop=True)

    output = OUTPUT_DIR / "airguard_prediksi_besok.csv"
    hasil.to_csv(output, index=False)

    print(f"Tanggal input terakhir : {tanggal_terbaru:%Y-%m-%d}")
    print(f"Tanggal yang diprediksi: {(tanggal_terbaru + pd.Timedelta(days=1)):%Y-%m-%d}")
    print(f"Jumlah wilayah        : {len(hasil)}")
    print("Distribusi prediksi:")
    print(hasil["kategori_prediksi"].value_counts())
    print(f"Tersimpan di          : {output}")
    return hasil


def evaluasi_test(df: pd.DataFrame, bundle):
    """Ulangi evaluasi pada periode test, tanpa melatih ulang model."""
    fitur = bundle["fitur"]
    model = bundle["model"]
    target = "kategori_target_pm2_5"

    if target not in df.columns:
        raise KeyError(f"Kolom target '{target}' tidak tersedia pada data.")

    data_test = df[df["tanggal"] >= TEST_START].copy()
    data_test = data_test.dropna(subset=[target])
    X_test = siapkan_fitur(data_test, fitur)

    # Model disimpan dengan label numerik. Jika target berupa teks, gunakan
    # label_map dari bundle agar urutannya sama seperti saat training.
    label_map = bundle.get("label_map", {})
    if label_map:
        y_test = data_test[target].map(label_map)
        if y_test.isna().any():
            raise ValueError("Ada label target test yang tidak ada di label_map model.")
        y_test = y_test.astype(int).to_numpy()
    else:
        y_test = data_test[target].to_numpy()

    y_pred = model.predict(X_test)
    proba = model.predict_proba(X_test)

    print(f"Periode test: {data_test['tanggal'].min():%Y-%m-%d} sampai "
          f"{data_test['tanggal'].max():%Y-%m-%d}")
    print(f"Jumlah baris: {len(data_test)}")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred):.4f}")
    print(f"Macro F1: {f1_score(y_test, y_pred, average='macro'):.4f}")
    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            y_pred,
            labels=sorted(label_map.values()) if label_map else None,
            target_names=[
                nama_label(bundle, kelas)
                for kelas in sorted(label_map.values())
            ] if label_map else None,
            zero_division=0,
            digits=4,
        )
    )
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    hasil = data_test[
        ["kode_kabkota", "nama_kabkota", "provinsi", "tanggal", "pm2_5", target]
    ].rename(
        columns={
            "tanggal": "tanggal_input",
            "pm2_5": "pm2_5_hari_ini",
            target: "kategori_aktual",
        }
    )
    hasil["tanggal_prediksi"] = hasil["tanggal_input"] + pd.Timedelta(days=1)
    hasil["kategori_prediksi"] = [nama_label(bundle, nilai) for nilai in y_pred]
    hasil = tambah_probabilitas(hasil, proba, bundle)

    output = OUTPUT_DIR / "airguard_uji_test.csv"
    hasil.to_csv(output, index=False)
    print(f"Hasil baris test tersimpan di: {output}")
    return hasil


def main():
    parser = argparse.ArgumentParser(description="Uji model klasifikasi AirGuard.")
    parser.add_argument(
        "--mode",
        choices=["besok", "test", "keduanya"],
        default="besok",
        help="besok=prediksi terbaru, test=evaluasi test, keduanya=jalankan keduanya",
    )
    args = parser.parse_args()

    try:
        bundle = baca_bundle()
        df = baca_data()
        print(f"Model: {bundle.get('nama_model', 'tidak tercatat')}")
        print(f"Data : {DATA_PATH}")
        print()

        if args.mode in ("besok", "keduanya"):
            prediksi_besok(df, bundle)
            print()
        if args.mode in ("test", "keduanya"):
            evaluasi_test(df, bundle)
    except (FileNotFoundError, KeyError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
