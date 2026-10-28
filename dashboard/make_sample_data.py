"""Membuat data CONTOH (sintetis) agar dashboard bisa dikembangkan sebelum output model tim siap.

Jalankan dari folder dashboard:  python make_sample_data.py
Angka yang dihasilkan bukan data nyata.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from utils import WILAYAH, nama_kategori

rng = np.random.default_rng(42)
out = Path(__file__).parent / "sample"
out.mkdir(exist_ok=True)

tanggal = pd.date_range("2025-08-01", "2026-10-21")
n = len(tanggal)
doy = tanggal.dayofyear.values
# Tingkat dasar sintetis: makin padat penduduk makin tinggi, ditambah selisih antarprovinsi.
OFFSET_PROV = {"DKI Jakarta": 14, "Banten": 8, "Jawa Barat": 6, "Jawa Timur": 3, "Jawa Tengah": 0, "DI Yogyakarta": -4}

pre_rows, pred_rows = [], []
for w in WILAYAH.itertuples():
    kota = w.kota
    b = 12 + 7 * np.log10(max(w.penduduk, 1e5) / 1e5) + OFFSET_PROV.get(w.provinsi, 0) + rng.normal(0, 2)
    b = max(b, 8)
    musim = 1 + 0.35 * np.cos(2 * np.pi * (doy - 230) / 365)
    angin = np.clip(rng.normal(3.5, 1.2, n), 0.5, None)
    hujan = np.clip(rng.gamma(0.6, 6, n) * (1.7 - musim), 0, None)
    e = np.zeros(n)
    for i in range(1, n):
        e[i] = 0.7 * e[i - 1] + rng.normal(0, 0.12)
    pm = np.clip(b * musim * (1 + e) * (1 - 0.05 * (angin - 3.5)) - 0.15 * hujan, 3, None)

    pre_rows.append(pd.DataFrame({
        "kota": kota, "tanggal": tanggal, "pm2_5": pm.round(1),
        "temperature_2m": (27 + 2 * np.sin(doy / 58) + rng.normal(0, 0.8, n)).round(1),
        "relative_humidity_2m": np.clip(78 - 0.8 * (pm - b) + rng.normal(0, 4, n), 40, 100).round(0),
        "precipitation": hujan.round(1),
        "wind_speed_10m": angin.round(1),
        "surface_pressure": (1010 + rng.normal(0, 1.5, n)).round(1),
        "cloud_cover": np.clip(rng.normal(60, 22, n), 0, 100).round(0),
    }))

    prediksi = pm * (1 + rng.normal(0, 0.09, n))
    df = pd.DataFrame({"kota": kota, "tanggal_prediksi": tanggal,
                       "pm2_5_aktual": pm.round(1), "pm2_5_prediksi": prediksi.round(1)})
    besok = pd.DataFrame({"kota": [kota], "tanggal_prediksi": [tanggal[-1] + pd.Timedelta(days=1)],
                          "pm2_5_aktual": [np.nan],
                          "pm2_5_prediksi": [round(float(pm[-1] * (1 + rng.normal(0.02, 0.05))), 1)]})
    pred_rows.append(pd.concat([df, besok], ignore_index=True))

pre = pd.concat(pre_rows, ignore_index=True)
pred = pd.concat(pred_rows, ignore_index=True)
pred["error"] = (pred["pm2_5_prediksi"] - pred["pm2_5_aktual"]).round(2)
pred["abs_error"] = pred["error"].abs()
pred["kategori_risiko"] = pred["pm2_5_prediksi"].map(nama_kategori)

pre.to_csv(out / "airguard_preprocessed.csv", index=False)
pred.to_csv(out / "airguard_predictions.csv", index=False)

pd.DataFrame({
    "model": ["Persistence (baseline)", "Rata-rata 7 hari (baseline)", "RandomForest",
              "ExtraTrees", "HistGradientBoosting"],
    "MAE": [6.2, 7.4, 4.9, 5.1, 4.8],
    "RMSE": [9.1, 10.3, 7.5, 7.8, 7.3],
    "R2": [0.71, 0.64, 0.81, 0.80, 0.82],
}).to_csv(out / "model_metrics.csv", index=False)

pd.DataFrame({
    "feature": ["pm2_5_lag_1", "pm2_5_rolling_7", "pm2_5", "pm2_5_rolling_3", "bulan",
                "wind_speed_10m", "pm2_5_lag_7", "relative_humidity_2m", "precipitation", "temperature_2m"],
    "importance": [0.41, 0.19, 0.12, 0.08, 0.06, 0.04, 0.03, 0.03, 0.02, 0.02],
}).to_csv(out / "feature_importance.csv", index=False)

print("Data contoh dibuat di", out)
