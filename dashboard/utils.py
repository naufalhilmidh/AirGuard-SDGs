"""Konfigurasi bersama dan pemuat data untuk dashboard AirGuard SDGs."""
import re
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DATA_DIR = ROOT.parent / "data" / "data_gabungan"
SAMPLE_DIR = ROOT / "sample"

# Daftar final kabupaten/kota Pulau Jawa (119 wilayah, 6 provinsi).
WILAYAH_CSV = ROOT / "referensi" / "kabkota_pulau_jawa.csv"


def _muat_wilayah() -> pd.DataFrame:
    w = pd.read_csv(WILAYAH_CSV, dtype={"kode_provinsi": str, "kode_kabkota": str})
    for kol in w.select_dtypes("object"):
        w[kol] = w[kol].str.strip()  # ada spasi/tab nyasar di beberapa baris
    w = w.dropna(subset=["nama_kabkota"]).rename(columns={"nama_kabkota": "kota"})
    return w[["kode_kabkota", "kota", "provinsi", "tipe", "ibukota", "latitude", "longitude", "penduduk"]]


WILAYAH = _muat_wilayah()
KOTA = {r.kota: (r.latitude, r.longitude) for r in WILAYAH.itertuples()}
PROVINSI = list(dict.fromkeys(WILAYAH.sort_values("kode_kabkota")["provinsi"]))
PROV_DARI_KOTA = dict(zip(WILAYAH["kota"], WILAYAH["provinsi"]))

# Kategori risiko berdasarkan ISPU untuk PM2.5 (rata-rata 24 jam, ug/m3).
# CATATAN: cek ulang angka ini ke peraturan resminya (Permen LHK No. 14/2020)
# sebelum dikutip di makalah. Kategori ini adalah aturan visualisasi proyek,
# bukan klaim medis.
KATEGORI = [
    (15.5, "Baik", "#3A9D82"),
    (55.4, "Sedang", "#E3B341"),
    (150.4, "Tidak sehat", "#D9622B"),
    (250.4, "Sangat tidak sehat", "#A23B3B"),
    (float("inf"), "Berbahaya", "#5B2A4A"),
]
URUTAN_KATEGORI = [k[1] for k in KATEGORI]
WARNA_KATEGORI = {k[1]: k[2] for k in KATEGORI}
BATAS_TINGGI = KATEGORI[1][0]  # di atas nilai ini masuk "Tidak sehat"

WARNA_UTAMA = "#0F5C55"
WARNA_PREDIKSI = "#D9622B"
PALET_KOTA = ["#0F5C55", "#D9622B", "#3B6EA5", "#8A6D3B", "#6B5B95",
              "#4A8F3C", "#B0467A", "#5C6B73", "#C49A00", "#2A9DB0"]

WARNA_PROVINSI = dict(zip(PROVINSI, ["#0F5C55", "#D9622B", "#3B6EA5", "#8A6D3B", "#6B5B95", "#B0467A"]))

CUACA = {
    "temperature_2m": "Suhu (°C)",
    "relative_humidity_2m": "Kelembapan (%)",
    "precipitation": "Curah hujan (mm)",
    "wind_speed_10m": "Kecepatan angin (km/jam)",
    "surface_pressure": "Tekanan udara (hPa)",
    "cloud_cover": "Tutupan awan (%)",
}


def nama_kategori(nilai: float) -> str:
    for batas, nama, _ in KATEGORI:
        if nilai <= batas:
            return nama
    return KATEGORI[-1][1]


def _kunci(nama: str) -> str:
    n = str(nama).strip().lower()
    return re.sub(r"^(kabupaten|kab\.?|kota administrasi|kota)\s+", "", n)


def _samakan_nama(df: pd.DataFrame):
    """Petakan kolom kota di data tim ke nama resmi di daftar wilayah.

    Urutan pencocokan: kolom kode_kabkota (kalau ada), nama persis, lalu nama tanpa
    awalan Kota/Kabupaten (kalau kembar, "Kota X" diutamakan). Mengembalikan data yang
    sudah cocok dan daftar nama yang tidak ketemu.
    """
    if "kode_kabkota" in df.columns:
        peta = dict(zip(WILAYAH["kode_kabkota"], WILAYAH["kota"]))
        baru = df["kode_kabkota"].astype(str).str.strip().map(peta)
    else:
        persis = {k.lower(): k for k in WILAYAH["kota"]}
        tanpa = {}
        for k in sorted(WILAYAH["kota"], key=lambda x: not x.startswith("Kota")):
            tanpa.setdefault(_kunci(k), k)
        baru = df["kota"].map(lambda x: persis.get(str(x).strip().lower(), tanpa.get(_kunci(x))))
    tak_cocok = sorted(df.loc[baru.isna(), "kota"].astype(str).unique())
    df = df.assign(kota=baru).dropna(subset=["kota"])
    df["provinsi"] = df["kota"].map(PROV_DARI_KOTA)
    return df, tak_cocok


@st.cache_resource(show_spinner="Memuat data...")
def muat_data():
    """Baca file output tim. Kalau belum ada, pakai data contoh di dashboard/sample."""
    memakai_contoh = False

    def baca(nama, **kw):
        nonlocal memakai_contoh
        asli = DATA_DIR / nama
        if asli.exists():
            return pd.read_csv(asli, **kw)
        memakai_contoh = True
        return pd.read_csv(SAMPLE_DIR / nama, **kw)

    pred = baca("airguard_predictions.csv", parse_dates=["tanggal_prediksi"])
    pre = baca("airguard_preprocessed.csv", parse_dates=["tanggal"])
    metrik = baca("model_metrics.csv")
    fitur = baca("feature_importance.csv")

    pred, tak1 = _samakan_nama(pred)
    pre, tak2 = _samakan_nama(pre)
    # Kolom teks dijadikan kategori supaya filter (isin) dan groupby cepat untuk ratusan ribu baris.
    for df in (pred, pre):
        df["kota"] = df["kota"].astype("category")
        df["provinsi"] = df["provinsi"].astype("category")
    return pred, pre, metrik, fitur, memakai_contoh, sorted(set(tak1) | set(tak2))