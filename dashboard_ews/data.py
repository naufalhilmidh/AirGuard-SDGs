"""Konfigurasi bersama dan pemuat data untuk dashboard EWS AirGuard SDGs.

Sumber data, urut prioritas:
1. File tim di data/data_gabungan (airguard_preprocessed.csv, airguard_predictions.csv, ...).
2. Kalau airguard_preprocessed.csv ada tetapi airguard_predictions.csv belum: prediksi besok
   diganti baseline persistence (besok = hari ini) yang dihitung dari data asli. Ini BUKAN
   model tim, dan ditandai jelas di dashboard.
3. Kalau tidak ada file tim sama sekali: data contoh sintetis dari dashboard/sample.
Data asli dan data contoh tidak pernah dicampur.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
REPO = ROOT.parent
DATA_DIR = REPO / "data" / "data_gabungan"
SAMPLE_DIRS = [ROOT / "sample", REPO / "dashboard" / "sample"]
WILAYAH_CSV = ROOT / "referensi" / "kabkota_pulau_jawa.csv"

# ---------- Status EWS (3 tingkat, sesuai rincian desain) ----------
# Batas atas inklusif: Baik <= 15.0, Sedang 15.1 - 55.0, Tidak sehat > 55.0 (ug/m3).
BATAS = [15.0, 55.0]
EWS = [
    {"kode": 0, "nama": "Baik", "sebutan": "Aman", "warna": "#10B981", "teks": "#04271A", "rentang": "sampai 15,0 µg/m³"},
    {"kode": 1, "nama": "Sedang", "sebutan": "Waspada", "warna": "#F59E0B", "teks": "#3A2200", "rentang": "15,1 sampai 55,0 µg/m³"},
    {"kode": 2, "nama": "Tidak sehat", "sebutan": "Bahaya", "warna": "#EF4444", "teks": "#FFFFFF", "rentang": "di atas 55,0 µg/m³"},
]
BATAS_BAHAYA = BATAS[1]
LABEL_STATUS = {
    "Baik (Aman)": 0,
    "Sedang (Waspada)": 1,
    "Tidak Sehat (Bahaya)": 2,
    "Baik": 0,
    "Sedang": 1,
    "Tidak Sehat": 2,
}


def kode_status(nilai):
    """0 = Baik, 1 = Sedang, 2 = Tidak sehat. Menerima angka tunggal atau array."""
    return np.digitize(nilai, BATAS, right=True)


# ---------- Daftar wilayah ----------
def _muat_wilayah() -> pd.DataFrame:
    w = pd.read_csv(WILAYAH_CSV, dtype={"kode_provinsi": str, "kode_kabkota": str})
    for kol in w.select_dtypes("object"):
        w[kol] = w[kol].str.strip()
    w = w.dropna(subset=["nama_kabkota"]).rename(columns={"nama_kabkota": "kota"})
    return w[["kode_kabkota", "kota", "provinsi", "tipe", "latitude", "longitude", "penduduk"]]


WILAYAH = _muat_wilayah()
PROVINSI = list(dict.fromkeys(WILAYAH.sort_values("kode_kabkota")["provinsi"]))
PROV_DARI_KOTA = dict(zip(WILAYAH["kota"], WILAYAH["provinsi"]))
TIPE = dict(zip(WILAYAH["kota"], WILAYAH["tipe"]))
PENDUDUK = dict(zip(WILAYAH["kota"], WILAYAH["penduduk"]))
WARNA_PROVINSI = dict(zip(PROVINSI, ["#1E3A8A", "#0EA5E9", "#7C3AED", "#0F766E", "#B45309", "#BE185D"]))


CUACA = {
    "temperature_2m": "Suhu (°C)",
    "relative_humidity_2m": "Kelembapan (%)",
    "precipitation": "Curah hujan (mm)",
    "wind_speed_10m": "Kecepatan angin (km/jam)",
    "surface_pressure": "Tekanan udara (hPa)",
    "cloud_cover": "Tutupan awan (%)",
}


# Faktor yang dikorelasikan dengan PM2.5. Hanya kolom yang benar-benar ada di data yang dipakai.
POLUTAN = {
    "pm10": "PM10 (µg/m³)",
    "carbon_monoxide": "Karbon monoksida (µg/m³)",
    "nitrogen_dioxide": "Nitrogen dioksida (µg/m³)",
    "sulphur_dioxide": "Sulfur dioksida (µg/m³)",
    "ozone": "Ozon (µg/m³)",
}


def faktor_tersedia(kolom) -> dict:
    """Faktor cuaca dan polutan lain yang ada di kolom data (urutan tetap)."""
    return {k: v for k, v in {**CUACA, **POLUTAN}.items() if k in kolom}


def nama_pendek(n: str) -> str:
    n = n.replace("Kota Administrasi ", "").replace("Kabupaten Administrasi ", "")
    if n.startswith("Kota "):
        return n[5:]
    if n.startswith("Kabupaten "):
        return "Kab. " + n[10:]
    return n


def kota_terbesar(daftar):
    """Kota (bukan kabupaten) berpenduduk terbanyak; kalau tak ada kota, kabupaten terbesar."""
    pakai = [k for k in daftar if TIPE.get(k) == "Kota"] or list(daftar)
    return max(pakai, key=lambda k: PENDUDUK[k])


# ---------- Pencocokan nama wilayah di data tim ----------
def _kunci(nama: str) -> str:
    n = str(nama).strip().lower()
    return re.sub(r"^(kabupaten|kab\.?|kota administrasi|kota)\s+", "", n)


def _samakan_nama(df: pd.DataFrame):
    """Petakan kolom kota di data tim ke nama resmi. Prioritas: kode_kabkota, nama persis,
    lalu nama tanpa awalan Kota/Kabupaten ("Kota X" diutamakan kalau kembar)."""
    if "kode_kabkota" in df.columns:
        peta = dict(zip(WILAYAH["kode_kabkota"], WILAYAH["kota"]))
        # kode seperti 35.10 kadang terbaca 35.1 (nol belakang hilang): kembalikan jadi dua digit
        kode = df["kode_kabkota"].astype(str).str.strip().str.replace(r"^(\d+)\.(\d)$", r"\1.\g<2>0", regex=True)
        baru = kode.map(peta)
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


# ---------- Pemuat data ----------
KODE_STR = {"kode_kabkota": str}


def _asli(nama, **kw):
    """Baca file tim, atau None kalau belum ada."""
    p = DATA_DIR / nama
    return pd.read_csv(p, dtype=KODE_STR, **kw) if p.exists() else None


def _contoh(nama, **kw):
    for d in SAMPLE_DIRS:
        if (d / nama).exists():
            return pd.read_csv(d / nama, dtype=KODE_STR, **kw)
    raise FileNotFoundError(f"{nama} tidak ditemukan di data/data_gabungan maupun folder sample.")


def _kota(df):
    """Data asli memakai nama_kabkota; dashboard memakai kolom kota."""
    if "kota" not in df.columns and "nama_kabkota" in df.columns:
        df = df.rename(columns={"nama_kabkota": "kota"})
    return df


def _baseline(pre: pd.DataFrame) -> pd.DataFrame:
    """Prediksi persistence: PM2.5 esok hari dianggap sama dengan hari ini.

    aktual untuk tanggal d+1 diambil dari target_pm2_5 pada tanggal d. Satu baris tambahan per kota
    (tanggal terakhir + 2 hari) berisi prediksi untuk besok yang belum punya nilai aktual."""
    d = pre[["kota", "tanggal", "pm2_5", "target_pm2_5"]].sort_values(["kota", "tanggal"])
    d = d.assign(kota=d["kota"].astype(str))
    utama = pd.DataFrame({"kota": d["kota"], "tanggal_prediksi": d["tanggal"] + pd.Timedelta(days=1),
                          "pm2_5_prediksi": d["pm2_5"], "pm2_5_aktual": d["target_pm2_5"]})
    akhir = d.groupby("kota", as_index=False).tail(1)
    depan = pd.DataFrame({"kota": akhir["kota"], "tanggal_prediksi": akhir["tanggal"] + pd.Timedelta(days=2),
                          "pm2_5_prediksi": akhir["target_pm2_5"], "pm2_5_aktual": np.nan})
    return pd.concat([utama, depan], ignore_index=True)


@st.cache_resource(show_spinner="Memuat data...")
def muat_data():
    """Mengembalikan (pred, pre, metrik, fitur, sumber, tak_cocok). Data tidak boleh diubah di tempat.

    sumber: "tim" (prediksi dari file tim), "baseline" (data asli, prediksi persistence) atau "contoh" (sintetis).
    metrik dan fitur bernilai None kalau tim belum menyediakannya.
    """
    pre = _asli("airguard_preprocessed.csv", parse_dates=["tanggal"])
    pred = _asli("airguard_predictions.csv", parse_dates=["tanggal_prediksi"])
    metrik = _asli("model_metrics.csv")
    fitur = _asli("feature_importance.csv")

    if pre is None and pred is None:
        sumber = "contoh"
        pre = _contoh("airguard_preprocessed.csv", parse_dates=["tanggal"])
        pred = _contoh("airguard_predictions.csv", parse_dates=["tanggal_prediksi"])
        metrik, fitur = _contoh("model_metrics.csv"), _contoh("feature_importance.csv")
    else:
        if pre is None:
            pre = _contoh("airguard_preprocessed.csv", parse_dates=["tanggal"])
        sumber = "tim"

    pre, tak2 = _samakan_nama(_kota(pre))
    if pred is None:
        sumber, tak1 = "baseline", []
        pred = _baseline(pre)
        pred["provinsi"] = pred["kota"].map(PROV_DARI_KOTA)
    else:
        pred, tak1 = _samakan_nama(_kota(pred))

    # Output terbaru tim adalah klasifikasi kategori, bukan prediksi angka.
    # Dashboard tetap memakai nama status internal yang sama, tetapi tidak
    # mengarang nilai pm2_5_prediksi dari kategori.
    mode_kategori = "kategori_prediksi" in pred.columns
    if mode_kategori:
        pred["st_prediksi"] = pred["kategori_prediksi"].map(LABEL_STATUS).fillna(-1).astype("int8")

        if "kategori_aktual" in pred.columns:
            pred["st_aktual"] = pred["kategori_aktual"].map(LABEL_STATUS).fillna(-1).astype("int8")
        else:
            pred["st_aktual"] = -1

        # Nilai aktual numerik diambil dari target preprocessed berdasarkan
        # tanggal target. Nilai prediksi numerik memang tidak tersedia.
        if "target_pm2_5" in pre.columns:
            aktual = pre[["kota", "tanggal", "target_pm2_5"]].copy()
            aktual["tanggal_prediksi"] = aktual["tanggal"] + pd.Timedelta(days=1)
            aktual = aktual[["kota", "tanggal_prediksi", "target_pm2_5"]]
            aktual = aktual.rename(columns={"target_pm2_5": "pm2_5_aktual"})
            pred = pred.drop(columns=["pm2_5_aktual"], errors="ignore").merge(
                aktual, on=["kota", "tanggal_prediksi"], how="left"
            )
        else:
            pred["pm2_5_aktual"] = np.nan
        pred["pm2_5_prediksi"] = np.nan
        pred.attrs["mode_kategori"] = True
    else:
        ada = pred["pm2_5_aktual"].notna()
        pred["st_aktual"] = np.where(ada, kode_status(pred["pm2_5_aktual"].fillna(0)), -1).astype("int8")
        pred["st_prediksi"] = kode_status(pred["pm2_5_prediksi"]).astype("int8")
        pred.attrs["mode_kategori"] = False

    for df in (pred, pre):  # kategori: filter dan groupby jauh lebih cepat
        df["kota"] = df["kota"].astype("category")
        df["provinsi"] = df["provinsi"].astype("category")
    return pred, pre, metrik, fitur, sumber, sorted(set(tak1) | set(tak2))


@st.cache_resource
def muat_klaster():
    """Hasil clustering tim (clustering_wilayah.csv) atau None kalau belum ada."""
    k = _asli("clustering_wilayah.csv")
    if k is None:
        return None
    k, _ = _samakan_nama(_kota(k))
    k["kota"] = k["kota"].astype(str)
    k["nama"] = k["kota"].map(nama_pendek)
    return k.reset_index(drop=True)


@st.cache_resource
def tabel_besok():
    """Satu baris per kabupaten/kota: PM2.5 hari ini, prediksi besok, status, angin."""
    pred, pre, *_ = muat_data()

    if pred.attrs.get("mode_kategori", False):
        # File ini dibuat oleh notebooks/04_modeling/uji_model_airguard.py.
        depan = _asli("airguard_prediksi_besok.csv", parse_dates=["tanggal_input", "tanggal_prediksi"])
        if depan is None:
            raise FileNotFoundError(
                "Mode klasifikasi membutuhkan airguard_prediksi_besok.csv. "
                "Jalankan uji_model_airguard.py --mode besok terlebih dahulu."
            )
        depan, _ = _samakan_nama(_kota(depan))
        depan["status"] = depan["kategori_prediksi"].map(LABEL_STATUS).astype("int8")
        t = depan[["kota", "tanggal_input", "tanggal_prediksi", "pm2_5_hari_ini", "status"]].copy()
        t = t.rename(columns={"pm2_5_hari_ini": "pm_ini"})
        t["pm_besok"] = np.nan
        t["perubahan"] = np.nan
        akhir = t["tanggal_input"].max()
        besok = t["tanggal_prediksi"].max()
        if "wind_speed_10m" in pre.columns:
            w = pre[pre["tanggal"] == akhir].set_index("kota")["wind_speed_10m"]
            w.index = w.index.astype(str)
            t["angin_kmh"] = t["kota"].astype(str).map(w)
        else:
            t["angin_kmh"] = np.nan
        t = t.merge(WILAYAH, on="kota", how="left")
        t["provinsi"] = t["provinsi"].astype(str)
        t["nama"] = t["kota"].map(nama_pendek)
        return t.rename(columns={"latitude": "lat", "longitude": "lon"}), akhir, besok

    akhir = pred.loc[pred["pm2_5_aktual"].notna(), "tanggal_prediksi"].max()
    besok = akhir + pd.Timedelta(days=1)
    ini = pred[pred["tanggal_prediksi"] == akhir].set_index("kota")["pm2_5_aktual"]
    bsk = pred[pred["tanggal_prediksi"] == besok].set_index("kota")["pm2_5_prediksi"]
    t = pd.DataFrame({"pm_ini": ini, "pm_besok": bsk}).dropna().reset_index()
    t["kota"] = t["kota"].astype(str)
    if "wind_speed_10m" in pre.columns:
        w = pre[pre["tanggal"] == akhir].set_index("kota")["wind_speed_10m"]
        w.index = w.index.astype(str)
        t["angin_kmh"] = t["kota"].map(w)
    else:
        t["angin_kmh"] = np.nan
    t = t.merge(WILAYAH, on="kota", how="left")
    t["provinsi"] = t["provinsi"].astype(str)
    t["nama"] = t["kota"].map(nama_pendek)
    t["status"] = kode_status(t["pm_besok"]).astype(int)
    t["perubahan"] = t["pm_besok"] - t["pm_ini"]
    return t.rename(columns={"latitude": "lat", "longitude": "lon"}), akhir, besok


@st.cache_resource
def ringkasan_data():
    """Angka ringkasan untuk beranda, semuanya dihitung dari data."""
    pred, pre, *_ = muat_data()
    ada = pred["st_aktual"] >= 0
    kota_data = set(pred["kota"].astype(str).unique())
    return {
        "n_kota": len(kota_data),
        "n_provinsi": pred["provinsi"].nunique(),
        "penduduk_juta": sum(PENDUDUK[k] for k in kota_data) / 1e6,
        "n_hari": int(pre["tanggal"].nunique()),
        "awal": pre["tanggal"].min(),
        "akhir": pre["tanggal"].max(),
        "akurasi": float((pred.loc[ada, "st_aktual"] == pred.loc[ada, "st_prediksi"]).mean()),
        "n_uji": int(ada.sum()),
    }


@st.cache_resource
def cakupan_provinsi():
    """Berapa kabupaten/kota per provinsi yang punya data dibanding daftar resmi."""
    pred, *_ = muat_data()
    ada = set(pred["kota"].astype(str).unique())
    return {p: (sum(k in ada for k in WILAYAH.loc[WILAYAH["provinsi"] == p, "kota"]),
                int((WILAYAH["provinsi"] == p).sum())) for p in PROVINSI}


# ---------- Proyeksi jangka panjang ----------
@st.cache_resource(show_spinner="Menyiapkan proyeksi...")
def muat_proyeksi():
    """Prakiraan harian sampai akhir tahun depan.

    Kalau tim menyediakan data/data_gabungan/airguard_forecast.csv (kolom: kota, tanggal,
    pm2_5_prakiraan, opsional batas_bawah dan batas_atas) file itu yang dipakai. Kalau tidak,
    proyeksi dihitung dari pola musiman riwayat (rata-rata per hari-dalam-tahun per kota),
    yang BUKAN hasil model machine learning.
    """
    pred, pre, *_ = muat_data()
    akhir = pred.loc[pred["pm2_5_aktual"].notna(), "tanggal_prediksi"].max()
    tahun = akhir.year + 1
    tanggal = pd.date_range(akhir + pd.Timedelta(days=1), f"{tahun}-12-31")

    berkas = DATA_DIR / "airguard_forecast.csv"
    if berkas.exists():
        f = pd.read_csv(berkas, parse_dates=["tanggal"])
        f, _ = _samakan_nama(f)
        f = f[f["tanggal"].isin(tanggal)].copy()
        f["batas_bawah"] = f["batas_bawah"] if "batas_bawah" in f else np.nan
        f["batas_atas"] = f["batas_atas"] if "batas_atas" in f else np.nan
        f["kota"] = f["kota"].astype(str)
        return f[["kota", "provinsi", "tanggal", "pm2_5_prakiraan", "batas_bawah", "batas_atas"]], "tim", akhir, tahun

    h = pre[["kota", "tanggal", "pm2_5"]].copy()
    h["kota"] = h["kota"].astype(str)
    h["doy"] = h["tanggal"].dt.dayofyear.clip(upper=365)
    m = h.groupby(["kota", "doy"])["pm2_5"].agg(["mean", "std"]).reset_index()
    kotas = sorted(m["kota"].unique())

    def halus(kolom):
        p = m.pivot(index="kota", columns="doy", values=kolom).reindex(index=kotas, columns=range(1, 366))
        p = p.T.interpolate(limit_direction="both").T
        arr = np.nan_to_num(p.to_numpy(), nan=float(np.nanmean(p.to_numpy())))
        ext = np.concatenate([arr[:, -7:], arr, arr[:, :7]], axis=1)  # melingkar: akhir tahun nyambung ke awal
        return pd.DataFrame(ext.T).rolling(15).mean().to_numpy()[14:].T

    rata, sebar = halus("mean"), halus("std")
    idx = np.minimum(tanggal.dayofyear.to_numpy(), 365) - 1
    hat = rata[:, idx]
    sd = sebar[:, idx]
    n, T = len(kotas), len(tanggal)
    f = pd.DataFrame({
        "kota": np.repeat(kotas, T), "tanggal": np.tile(tanggal.to_numpy(), n),
        "pm2_5_prakiraan": hat.ravel(),
        "batas_bawah": np.clip(hat - sd, 0, None).ravel(), "batas_atas": (hat + sd).ravel(),
    })
    f["provinsi"] = f["kota"].map(PROV_DARI_KOTA)
    return f, "musiman", akhir, tahun
