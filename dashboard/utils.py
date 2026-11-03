"""Konfigurasi bersama dan pemuat data untuk dashboard AirGuard SDGs."""
import json
import math
import re
from pathlib import Path

import numpy as np
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

# Kode BPS: kunci untuk mencocokkan poligon batas wilayah pada peta.
KODE_DARI_KOTA = dict(zip(WILAYAH["kota"], WILAYAH["kode_kabkota"]))
KODE_DARI_PROV = dict(zip(WILAYAH["provinsi"], WILAYAH["kode_kabkota"].str[:2]))  # 31.01 -> 31
BATAS_DIR = ROOT / "referensi"


@st.cache_data(show_spinner=False)
def muat_batas(level: str = "kabkota"):
    """Poligon batas wilayah dari referensi/buat_batas.py; None kalau berkasnya belum ada."""
    nama = "batas_kabkota_jawa.geojson" if level == "kabkota" else "batas_provinsi_jawa.geojson"
    berkas = BATAS_DIR / nama
    if not berkas.exists():
        return None
    return json.loads(berkas.read_text(encoding="utf-8"))

# Status EWS AirGuard: 3 tingkat berdasarkan PM2.5 harian (ug/m3), batas atas inklusif:
# Baik <= 15,0 | Sedang 15,1 - 55,0 | Tidak sehat > 55,0. Ini aturan visualisasi proyek
# (rincian desain), bukan klaim medis. Cek ulang ke peraturan resmi sebelum dikutip di makalah.
KATEGORI = [
    (15.0, "Baik", "#2E9E5B"),
    (55.0, "Sedang", "#E8B93B"),
    (float("inf"), "Tidak sehat", "#C4342A"),
]
URUTAN_KATEGORI = [k[1] for k in KATEGORI]
WARNA_KATEGORI = {k[1]: k[2] for k in KATEGORI}
BATAS_TINGGI = KATEGORI[1][0]  # di atas nilai ini masuk "Tidak sehat"
BATAS_STATUS = [KATEGORI[0][0], KATEGORI[1][0]]


def kode_status(nilai):
    """0 = Baik, 1 = Sedang, 2 = Tidak sehat. Menerima angka tunggal atau array."""
    return np.digitize(nilai, BATAS_STATUS, right=True)

WARNA_UTAMA = "#0F5C55"
WARNA_PREDIKSI = "#D9622B"
PALET_KOTA = ["#0F5C55", "#D9622B", "#3B6EA5", "#8A6D3B", "#6B5B95",
              "#4A8F3C", "#B0467A", "#5C6B73", "#C49A00", "#2A9DB0"]

WARNA_PROVINSI = dict(zip(PROVINSI, ["#0F5C55", "#D9622B", "#3B6EA5", "#8A6D3B", "#6B5B95", "#B0467A"]))

# Variabel pembanding PM2.5 di tab "Faktor Lain". Dataset 119 kabupaten/kota Pulau
# Jawa (airguard_preprocessed.csv) tidak memuat variabel cuaca, jadi yang dipakai
# adalah polutan lain dan riwayat PM2.5 itu sendiri.
FAKTOR = {
    "pm10": "PM10 (µg/m³)",
    "nitrogen_dioxide": "NO₂ (µg/m³)",
    "sulphur_dioxide": "SO₂ (µg/m³)",
    "carbon_monoxide": "CO (µg/m³)",
    "ozone": "Ozon (µg/m³)",
    "pm2_5_lag_1": "PM2.5 kemarin",
    "pm2_5_rolling_7": "Rata-rata PM2.5 7 hari",
}


def nama_kategori(nilai: float) -> str:
    for batas, nama, _ in KATEGORI:
        if nilai <= batas:
            return nama
    return KATEGORI[-1][1]


# Zona cluster wilayah: K-Means k=3 atas 10 fitur jangka panjang per kabupaten/kota
# (notebooks/04_modeling/CLUSTERING.ipynb). Ini ANALISIS TERPISAH dari peta risiko harian:
# sifatnya per wilayah, tidak berubah per tanggal. Warna sengaja beda keluarga (ungu) dari
# palet kategori supaya dua legenda tidak tertukar (requirement.md bagian 6.5 dan 6.6).
LABEL_ZONA = {
    "rendah-stabil": "Rendah – stabil",
    "sedang-musiman": "Sedang – musiman",
    "tinggi-persisten": "Tinggi – persisten",
}
WARNA_ZONA = {
    "rendah-stabil": "#2E9E5B",
    "sedang-musiman": "#E8B93B",
    "tinggi-persisten": "#C4342A",
}
URUTAN_ZONA = ["rendah-stabil", "sedang-musiman", "tinggi-persisten"]

# Titik henti gradasi peta: hijau di 0, lalu warna kategori berikutnya di setiap ambang ISPU.
RAMP_WARNA = [(0.0, KATEGORI[0][2])] + [(KATEGORI[i][0], KATEGORI[i + 1][2])
                                        for i in range(len(KATEGORI) - 1)]


def campur_warna(w1: str, w2: str, t: float) -> str:
    """Campur dua warna hex: t=0 menghasilkan w1, t=1 menghasilkan w2."""
    a = [int(w1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(w2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def warna_nilai(nilai) -> str:
    """Warna gradasi hijau -> kuning -> merah untuk satu nilai PM2.5.

    Dihitung langsung di Python, bukan lewat colorscale plotly: warna dari colorscale terbukti
    bisa melenceng dari legenda, jadi peta memakai warna literal per wilayah seperti ini.
    """
    try:
        v = float(nilai)
    except (TypeError, ValueError):
        return "#D8D8D8"
    if v != v:  # NaN
        return "#D8D8D8"
    for (b1, w1), (b2, w2) in zip(RAMP_WARNA, RAMP_WARNA[1:]):
        if v <= b2:
            return campur_warna(w1, w2, max(0.0, (v - b1) / (b2 - b1)))
    return RAMP_WARNA[-1][1]


@st.cache_data(show_spinner=False)
def jalur_peta(level: str = "kabkota"):
    """Poligon siap gambar sebagai SVG (proyeksi equirectangular, viewBox 1000 x H).

    Geometri tidak berubah, jadi dihitung sekali per level lalu dipakai ulang tiap rerun.
    """
    b = muat_batas(level)
    if b is None:
        return None
    fitur = b["features"]

    def poligon(g):
        return g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]

    lon_min = lat_min = float("inf")
    lon_max = lat_max = float("-inf")
    for f in fitur:
        for p in poligon(f["geometry"]):
            for ring in p:
                for lon, lat in ring:
                    lon_min, lon_max = min(lon_min, lon), max(lon_max, lon)
                    lat_min, lat_max = min(lat_min, lat), max(lat_max, lat)

    kx = math.cos(math.radians((lat_min + lat_max) / 2))  # koreksi lebar di lintang Jawa
    skala = 1000.0 / ((lon_max - lon_min) * kx)
    hasil = []
    for f in fitur:
        bagian = []
        for p in poligon(f["geometry"]):
            for ring in p:
                titik, terakhir = [], None
                for lon, lat in ring:
                    x, y = (lon - lon_min) * kx * skala, (lat_max - lat) * skala
                    # buang titik yang lebih rapat dari 0,6 satuan viewBox (~0,6 km): di layar
                    # jaraknya di bawah 1 piksel, tapi jumlah titiknya turun drastis sehingga
                    # spek plotly jauh lebih ringan
                    if terakhir and math.hypot(x - terakhir[0], y - terakhir[1]) < 0.6:
                        continue
                    titik.append(f"{x:.1f} {y:.1f}")
                    terakhir = (x, y)
                if len(titik) > 2:
                    bagian.append("M" + "L".join(titik) + "Z")
        hasil.append((f["properties"].get("kode"), f["properties"].get("nama", ""), "".join(bagian)))
    return {"lebar": 1000.0, "tinggi": (lat_max - lat_min) * skala, "fitur": hasil}


def urai_path(d: str):
    """Urai path 'M x y L x y ... Z' (boleh banyak subpath) jadi daftar poligon."""
    hasil = []
    for sub in d.split("M"):
        titik = []
        for pasangan in sub.strip().rstrip("Z").strip().split("L"):
            x, _, y = pasangan.strip().partition(" ")
            if x and y:
                titik.append((float(x), float(y)))
        if len(titik) > 2:
            hasil.append(titik)
    return hasil


def kode_bps(kode) -> str:
    """Samakan kode BPS ke bentuk 'PP.KK' dua digit.

    CSV hasil clustering menyimpan '33.1' padahal kode resminya '33.10': pandas membuang nol
    di belakang saat menulis nilai float. Satu digit setelah titik karena itu selalu berarti
    kode aslinya berakhiran nol ('33.10', '35.20'), bukan berkode '01' — kode seperti '31.01'
    tetap ditulis dua digit karena float 31.01 tidak kehilangan nol di depan.
    Tanpa normalisasi ini, 5 wilayah gagal ketemu poligonnya.
    """
    teks = str(kode).strip()
    if "." in teks:
        prov, _, kab = teks.partition(".")
        if kab.isdigit():
            return f"{prov}.{kab + '0' if len(kab) == 1 else kab}"
    elif teks.isdigit() and len(teks) == 4:
        return f"{teks[:2]}.{teks[2:]}"
    return teks


@st.cache_data(show_spinner="Memuat zona cluster...")
def muat_cluster():
    """Zona cluster 119 wilayah. Mengembalikan None kalau hasil clustering belum ada."""
    berkas = DATA_DIR / "clustering_wilayah.csv"
    if not berkas.exists():
        return None
    df = pd.read_csv(berkas, dtype={"kode_kabkota": str})
    df["kode"] = df["kode_kabkota"].map(kode_bps)
    df["zona"] = df["nama_cluster"].astype(str).str.strip().str.lower()
    return df[["kode", "nama_kabkota", "zona", "rata_rata_pm25", "persentase_hari_tinggi"]]


def _kunci(nama: str) -> str:
    n = str(nama).strip().lower()
    return re.sub(r"^(kabupaten|kab\.?|kota administrasi|kota)\s+", "", n)


def _samakan_nama(df: pd.DataFrame):
    """Petakan kolom kota di data tim ke nama resmi di daftar wilayah.

    Urutan pencocokan: kolom kode_kabkota (kalau ada), nama persis, lalu nama tanpa
    awalan Kota/Kabupaten (kalau kembar, "Kota X" diutamakan). Mengembalikan data yang
    sudah cocok dan daftar nama yang tidak ketemu.
    """
    persis = {k.lower(): k for k in WILAYAH["kota"]}
    tanpa = {}
    for k in sorted(WILAYAH["kota"], key=lambda x: not x.startswith("Kota")):
        tanpa.setdefault(_kunci(k), k)

    def cocok_nama(x):
        return persis.get(str(x).strip().lower(), tanpa.get(_kunci(x)))

    # Nama kolom wilayah beda antar file tim: "kota" (data contoh dashboard) atau
    # "nama_kabkota" (airguard_preprocessed.csv 119 kabupaten/kota).
    kol_nama = "kota" if "kota" in df.columns else "nama_kabkota" if "nama_kabkota" in df.columns else None
    if kol_nama is None:
        raise KeyError("Data tidak punya kolom 'kota' maupun 'nama_kabkota'")

    if "kode_kabkota" in df.columns:
        peta = dict(zip(WILAYAH["kode_kabkota"], WILAYAH["kota"]))
        baru = df["kode_kabkota"].astype(str).str.strip().map(peta)
        # Kode bisa kehilangan nol di belakang kalau kolomnya terbaca sebagai angka
        # (32.10 -> 32.1); baris seperti itu diselamatkan lewat nama wilayahnya.
        kurang = baru.isna()
        if kurang.any():
            baru = baru.fillna(df.loc[kurang, kol_nama].map(cocok_nama))
    else:
        baru = df[kol_nama].map(cocok_nama)

    tak_cocok = sorted(df.loc[baru.isna(), kol_nama].astype(str).unique())
    df = df.assign(kota=baru).dropna(subset=["kota"])
    df["provinsi"] = df["kota"].map(PROV_DARI_KOTA)
    return df, tak_cocok


# ---------------------------------------------------------------------------
# Pemuat data
# ---------------------------------------------------------------------------
# Urutan sumber (data asli dan data contoh TIDAK PERNAH dicampur):
#  1. "tim"      : file tim di data/data_gabungan (airguard_predictions.csv dst.)
#  2. "baseline" : airguard_preprocessed.csv ada, prediksi belum -> prediksi besok = hari ini
#                  (persistence). Ini BUKAN model tim dan ditandai jelas di dashboard.
#  3. "contoh"   : data sintetis di dashboard/sample, kalau tidak ada file tim sama sekali.
KODE_STR = {"kode_kabkota": str, "kode_provinsi": str}


def _asli(nama, **kw):
    p = DATA_DIR / nama
    return pd.read_csv(p, dtype=KODE_STR, **kw) if p.exists() else None


def _contoh(nama, **kw):
    return pd.read_csv(SAMPLE_DIR / nama, dtype=KODE_STR, **kw)


def _kota(df):
    """Data asli memakai nama_kabkota; dashboard memakai kolom kota."""
    if "kota" not in df.columns and "nama_kabkota" in df.columns:
        df = df.rename(columns={"nama_kabkota": "kota"})
    return df


def _baseline(pre: pd.DataFrame) -> pd.DataFrame:
    """Prediksi persistence: PM2.5 esok hari dianggap sama dengan hari ini.

    Aktual untuk tanggal d+1 diambil dari target_pm2_5 pada tanggal d. Satu baris tambahan
    per kota (tanggal terakhir + 2 hari) berisi prediksi besok yang belum punya nilai aktual."""
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
    """Mengembalikan (pred, pre, metrik, fitur, sumber, tak_cocok).

    sumber: "tim", "baseline" atau "contoh". metrik dan fitur None kalau tim belum menyediakannya.
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

    ada = pred["pm2_5_aktual"].notna()
    pred["st_aktual"] = np.where(ada, kode_status(pred["pm2_5_aktual"].fillna(0)), -1).astype("int8")
    pred["st_prediksi"] = kode_status(pred["pm2_5_prediksi"]).astype("int8")

    for df in (pred, pre):  # kategori: filter (isin) dan groupby jauh lebih cepat
        df["kota"] = df["kota"].astype("category")
        df["provinsi"] = df["provinsi"].astype("category")
    return pred, pre, metrik, fitur, sumber, sorted(set(tak1) | set(tak2))


@st.cache_data(show_spinner=False)
def muat_cluster_rinci():
    """Hasil clustering lengkap per kab/kota (kolom: kota, provinsi, zona, ringkasan PM2.5) atau None."""
    k = _asli("clustering_wilayah.csv")
    if k is None:
        return None
    k, _ = _samakan_nama(_kota(k))
    k["kota"] = k["kota"].astype(str)
    k["zona"] = k["nama_cluster"].astype(str).str.strip().str.lower()
    return k.reset_index(drop=True)


def profil_unik(pre: pd.DataFrame) -> dict:
    """Berapa deret PM2.5 yang benar-benar berbeda. Data CAMS beresolusi grid, jadi beberapa
    kab/kota bertetangga memakai deret yang sama persis."""
    p = pre.pivot_table(index="tanggal", columns="kota", values="pm2_5", observed=True)
    unik = p.round(3).T.drop_duplicates().shape[0]
    return {"n_kota": p.shape[1], "n_unik": int(unik)}


# ---------------------------------------------------------------------------
# Proyeksi jangka panjang
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Menyiapkan proyeksi...")
def muat_proyeksi():
    """Prakiraan harian sampai akhir tahun depan: (tabel, metode, tanggal_terakhir_data, tahun).

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
        if "batas_bawah" not in f:
            f["batas_bawah"] = np.nan
        if "batas_atas" not in f:
            f["batas_atas"] = np.nan
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
    hat, sd = rata[:, idx], sebar[:, idx]
    n, T = len(kotas), len(tanggal)
    f = pd.DataFrame({
        "kota": np.repeat(kotas, T), "tanggal": np.tile(tanggal.to_numpy(), n),
        "pm2_5_prakiraan": hat.ravel(),
        "batas_bawah": np.clip(hat - sd, 0, None).ravel(), "batas_atas": (hat + sd).ravel(),
    })
    f["provinsi"] = f["kota"].map(PROV_DARI_KOTA)
    return f, "musiman", akhir, tahun
