"""Bangun file batas wilayah (GeoJSON) untuk dashboard AirGuard.

Jalankan sekali:  .venv\\Scripts\\python.exe referensi\\buat_batas.py

Sumber: geoBoundaries gbOpen IDN ADM1 & ADM2 (dibangun dari data Badan Pusat
Statistik / OCHA), lisensi CC BY 3.0 IGO. Yang diunduh versi "simplified",
lalu dipotong hanya untuk 6 provinsi di Pulau Jawa dan diberi properti `kode`
(kode BPS) supaya bisa di-join langsung dengan kabkota_pulau_jawa.csv.

Hasil:
  referensi/batas_kabkota_jawa.geojson   (119 poligon)
  referensi/batas_provinsi_jawa.geojson  (6 poligon)
"""
import json
import math
import re
from pathlib import Path

import pandas as pd
import requests

DIR = Path(__file__).parent
CSV = DIR / "kabkota_pulau_jawa.csv"
BASE = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IDN"

PREFIKS = ("kabupaten administrasi", "kota administrasi", "kabupaten", "kota")


def dasar(nama: str) -> str:
    """Nama tanpa awalan Kabupaten/Kota/Administrasi, hanya huruf kecil & angka."""
    n = str(nama).strip().lower()
    for p in PREFIKS:
        if n.startswith(p + " "):
            n = n[len(p):].strip()
            break
    return re.sub(r"[^a-z0-9]", "", n)


def tipe_geo(nama: str) -> str:
    return "Kota" if str(nama).strip().lower().startswith("kota") else "Kabupaten"


def unduh(level: str) -> dict:
    url = f"{BASE}/{level}/geoBoundaries-IDN-{level}_simplified.geojson"
    print(f"  unduh {level} ... ", end="", flush=True)
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    d = r.json()
    print(f"{len(r.content) / 1024 / 1024:.1f} MB, {len(d['features'])} fitur")
    return d


def bulat(geom, digit=4):
    """Bulatkan koordinat supaya file kecil; struktur geometri dipertahankan."""
    def bersih(c):
        if isinstance(c, (int, float)):
            return round(float(c), digit)
        return [bersih(x) for x in c]
    return {"type": geom["type"], "coordinates": bersih(geom["coordinates"])}


def titik_tengah(geom):
    """Titik tengah kasar dari bounding box (cukup untuk cadangan pencocokan)."""
    xs, ys = [], []

    def jelajah(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0])
            ys.append(c[1])
        else:
            for x in c:
                jelajah(x)

    jelajah(geom["coordinates"])
    return sum(ys) / len(ys), sum(xs) / len(xs)


def jarak_km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (0.5 - math.cos((lat2 - lat1) * p) / 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2)
    return 12742 * math.asin(math.sqrt(a))


def tulis(daftar, nama_file):
    fc = {"type": "FeatureCollection", "features": daftar}
    teks = json.dumps(fc, ensure_ascii=False, separators=(",", ":"))
    (DIR / nama_file).write_text(teks, encoding="utf-8")
    print(f"  tulis {nama_file}: {len(daftar)} fitur, {len(teks) / 1024:.0f} KB")


def main():
    w = pd.read_csv(CSV, dtype={"kode_provinsi": str, "kode_kabkota": str})
    for k in w.select_dtypes("object"):
        w[k] = w[k].astype(str).str.strip()
    w = w.dropna(subset=["nama_kabkota"])
    print(f"wilayah target: {len(w)} kabupaten/kota, {w['provinsi'].nunique()} provinsi")

    print("AMBIL DATA SUMBER")
    adm2 = unduh("ADM2")
    adm1 = unduh("ADM1")

    # ---- kabupaten/kota ----
    indeks = {}
    for f in adm2["features"]:
        nm = f["properties"]["shapeName"]
        kunci = (dasar(nm), tipe_geo(nm))
        indeks.setdefault(kunci, []).append(f)
    ganda = {k: v for k, v in indeks.items() if len(v) > 1}
    if ganda:
        print(f"  PERINGATAN: {len(ganda)} kunci ganda di sumber: {list(ganda)[:3]}")

    dipakai, hasil, gagal = set(), [], []
    for r in w.itertuples():
        kunci = (dasar(r.nama_kabkota), r.tipe)
        calon = [f for f in indeks.get(kunci, []) if id(f) not in dipakai]
        if len(calon) == 1:
            f = calon[0]
        else:
            # cadangan: poligon terdekat dari titik pusat wilayah
            semua = [f for v in indeks.values() for f in v if id(f) not in dipakai]
            if not semua:
                gagal.append(r.nama_kabkota)
                continue
            f = min(semua, key=lambda x: jarak_km(float(r.latitude), float(r.longitude),
                                                 *titik_tengah(x["geometry"])))
            print(f"  cocok-lewat-jarak: {r.nama_kabkota!r} -> {f['properties']['shapeName']!r}")
        dipakai.add(id(f))
        hasil.append({"type": "Feature",
                      "properties": {"kode": r.kode_kabkota, "nama": r.nama_kabkota},
                      "geometry": bulat(f["geometry"])})

    if gagal:
        print(f"  GAGAL mencocokkan {len(gagal)}: {gagal}")
    print(f"  cocok: {len(hasil)}/{len(w)}")
    tulis(hasil, "batas_kabkota_jawa.geojson")

    # ---- provinsi ----
    alias = {"DKI Jakarta": "Jakarta Special Capital Region",
             "DI Yogyakarta": "Special Region of Yogyakarta",
             "Jawa Barat": "West Java", "Jawa Tengah": "Central Java",
             "Jawa Timur": "East Java", "Banten": "Banten"}
    prov = adm1["features"]
    prop = sorted(w["provinsi"].unique())
    hasil_p = []
    for nm in prop:
        target = alias.get(nm, nm)
        f = next((x for x in prov if x["properties"]["shapeName"] == target), None)
        if f is None:
            pusat = w.loc[w["provinsi"] == nm, ["latitude", "longitude"]].astype(float).mean()
            f = min(prov, key=lambda x: jarak_km(pusat["latitude"], pusat["longitude"],
                                                *titik_tengah(x["geometry"])))
            print(f"  cocok-lewat-jarak: {nm!r} -> {f['properties']['shapeName']!r}")
        kode = str(w.loc[w["provinsi"] == nm, "kode_provinsi"].iloc[0])
        hasil_p.append({"type": "Feature",
                        "properties": {"kode": kode, "nama": nm},
                        "geometry": bulat(f["geometry"])})
    tulis(hasil_p, "batas_provinsi_jawa.geojson")


if __name__ == "__main__":
    main()
