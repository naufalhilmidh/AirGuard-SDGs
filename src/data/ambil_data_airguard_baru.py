"""Crawling kualitas udara Open-Meteo untuk 119 kabupaten/kota Pulau Jawa."""

import json
import random
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parents[2]
FILE_KABKOTA_UTAMA = BASE_DIR / "data" / "kabkota_pulau_jawa.csv"
FILE_KABKOTA_CADANGAN = BASE_DIR / "src" / "data" / "kabkota_pulau_jawa.csv"
FILE_KABKOTA = (
    FILE_KABKOTA_UTAMA
    if FILE_KABKOTA_UTAMA.exists()
    else FILE_KABKOTA_CADANGAN
)
DIR_MENTAH = BASE_DIR / "data" / "data_mentah"
DIR_GABUNGAN = BASE_DIR / "data" / "data_gabungan"
FILE_LOG = BASE_DIR / "log_kuota.json"

URL_UDARA = "https://air-quality-api.open-meteo.com/v1/air-quality"

TANGGAL_AWAL = date(2022, 8, 4)
TANGGAL_AKHIR = date.today() - timedelta(days=7)

# None berarti semua 119 kabupaten/kota.
BATAS_KABKOTA = None

# BATCH_SIZE hanya mengatur jumlah lokasi per request.
BATCH_SIZE = 10

BATAS_HARIAN = 9000
MAX_RETRY = 5
BACKOFF_AWAL = 30
BACKOFF_MAKS = 900

VARIABEL_UDARA = (
    "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,"
    "sulphur_dioxide,ozone"
)
VARIABEL_LIST = VARIABEL_UDARA.split(",")

KOLOM_INFO = [
    "kode_kabkota",
    "nama_kabkota",
    "provinsi",
    "tipe",
    "latitude",
    "longitude",
    "elevasi_m",
    "luas_km2",
    "penduduk",
]

DIR_MENTAH.mkdir(parents=True, exist_ok=True)
DIR_GABUNGAN.mkdir(parents=True, exist_ok=True)


def baca_kuota():
    if not FILE_LOG.exists():
        return 0.0

    try:
        data = json.loads(FILE_LOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0.0

    if data.get("tanggal") != str(date.today()):
        return 0.0

    return float(data.get("terpakai", 0))


def simpan_kuota(nilai):
    FILE_LOG.write_text(
        json.dumps({
            "tanggal": str(date.today()),
            "terpakai": nilai
        }),
        encoding="utf-8"
    )


def estimasi_bobot(mulai, akhir, jumlah_lokasi):
    jumlah_hari = (akhir - mulai).days + 1
    jumlah_variabel = len(VARIABEL_LIST)

    return (
        jumlah_lokasi
        * (jumlah_hari / 14)
        * (jumlah_variabel / 10)
    )


def sudah_mencakup(file_data, tanggal_akhir):
    """Mengecek apakah file sudah berisi data sampai tanggal akhir."""
    if not file_data.exists():
        return False

    try:
        waktu_terakhir = pd.to_datetime(
            pd.read_csv(file_data, usecols=["time"])["time"],
            errors="coerce"
        ).max()
    except (
        OSError,
        ValueError,
        KeyError,
        pd.errors.EmptyDataError
    ):
        return False

    return (
        pd.notna(waktu_terakhir)
        and waktu_terakhir.date() >= tanggal_akhir
    )


def ambil_batch(params):
    """Request serial dengan exponential backoff dan jitter."""
    for percobaan in range(1, MAX_RETRY + 1):
        try:
            response = requests.get(
                URL_UDARA,
                params=params,
                timeout=180
            )
        except requests.RequestException as error:
            if percobaan == MAX_RETRY:
                print("   koneksi gagal setelah retry:", error)
                return None, False

            waktu_backoff = min(
                BACKOFF_MAKS,
                BACKOFF_AWAL * (2 ** (percobaan - 1))
            )
            waktu_tunggu = waktu_backoff + random.uniform(0, 10)

            print(
                f"   koneksi gagal. Retry {percobaan}/{MAX_RETRY} "
                f"dalam {waktu_tunggu:.0f} detik."
            )
            time.sleep(waktu_tunggu)
            continue

        if response.status_code == 200:
            try:
                return response.json(), False
            except ValueError:
                print("   response bukan JSON valid")
                return None, False

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")

            try:
                waktu_server = (
                    float(retry_after)
                    if retry_after
                    else 0
                )
            except ValueError:
                waktu_server = 0

            waktu_backoff = min(
                BACKOFF_MAKS,
                BACKOFF_AWAL * (2 ** (percobaan - 1))
            )
            waktu_tunggu = max(
                waktu_server,
                waktu_backoff
            ) + random.uniform(0, 10)

            if percobaan == MAX_RETRY:
                print(
                    "   429 tetap muncul setelah semua retry. "
                    "Run dihentikan."
                )
                return None, True

            print(
                f"   429 rate limit. Retry {percobaan}/{MAX_RETRY} "
                f"dalam {waktu_tunggu:.0f} detik."
            )
            time.sleep(waktu_tunggu)
            continue

        print(
            f"   HTTP {response.status_code}: "
            f"{response.text[:250]}"
        )
        return None, False

    return None, True


def response_lokasi(response, indeks):
    if isinstance(response, list):
        return response[indeks]
    return response


def proses_lokasi(baris, hasil):
    frame = pd.DataFrame(hasil["hourly"])

    frame["grid_lat_udara"] = hasil.get("latitude")
    frame["grid_lon_udara"] = hasil.get("longitude")

    kode = str(baris["kode_kabkota"]).replace(".", "_")
    tujuan = DIR_MENTAH / f"udara_{kode}.csv"

    if tujuan.exists():
        data_lama = pd.read_csv(tujuan)

        frame = pd.concat(
            [data_lama, frame],
            ignore_index=True
        )

        frame = (
            frame
            .drop_duplicates(subset=["time"])
            .sort_values("time")
        )

    frame.to_csv(tujuan, index=False)


def ke_harian(baris, frame):
    frame["time"] = pd.to_datetime(frame["time"])
    frame["tanggal"] = frame["time"].dt.date

    kolom_nilai = [
        kolom for kolom in VARIABEL_LIST
        if kolom in frame.columns
    ]

    harian = (
        frame
        .groupby("tanggal", as_index=False)[kolom_nilai]
        .mean()
    )

    for indeks, kolom in enumerate(KOLOM_INFO):
        harian.insert(indeks, kolom, baris[kolom])

    return harian


kabkota = pd.read_csv(
    FILE_KABKOTA,
    encoding="utf-8-sig",
    dtype={"kode_kabkota": "string"}
)

for kolom in ["provinsi", "nama_kabkota", "tipe"]:
    kabkota[kolom] = kabkota[kolom].str.strip()

if BATAS_KABKOTA is not None:
    kabkota = kabkota.head(BATAS_KABKOTA)

print("Jumlah kab/kota   :", len(kabkota))
print("Periode           :", TANGGAL_AWAL, "sampai", TANGGAL_AKHIR)
print("Ukuran batch      :", BATCH_SIZE)

terpakai = baca_kuota()
print(
    "Estimasi kuota lokal:",
    round(terpakai),
    "dari batas",
    BATAS_HARIAN
)

berhenti = False

for nomor, awal in enumerate(
    range(0, len(kabkota), BATCH_SIZE),
    start=1
):
    batch = kabkota.iloc[awal:awal + BATCH_SIZE]

    perlu = []

    for baris in batch.to_dict("records"):
        kode = str(baris["kode_kabkota"]).replace(".", "_")
        file_data = DIR_MENTAH / f"udara_{kode}.csv"

        if not sudah_mencakup(
            file_data,
            TANGGAL_AKHIR
        ):
            perlu.append(baris)

    if not perlu:
        continue

    bobot = estimasi_bobot(
        TANGGAL_AWAL,
        TANGGAL_AKHIR,
        len(perlu)
    )

    if terpakai + bobot > BATAS_HARIAN:
        print(
            "Kuota lokal hampir habis. "
            "Lanjutkan pada hari berikutnya."
        )
        berhenti = True
        break

    print(
        f"Mengambil udara | seluruh periode | "
        f"batch {nomor} | {len(perlu)} lokasi"
    )

    params = {
        "latitude": ",".join(
            str(item["latitude"]) for item in perlu
        ),
        "longitude": ",".join(
            str(item["longitude"]) for item in perlu
        ),
        "hourly": VARIABEL_UDARA,
        "start_date": TANGGAL_AWAL.isoformat(),
        "end_date": TANGGAL_AKHIR.isoformat(),
        "timezone": "Asia/Jakarta",
        "domains": "cams_global",
    }

    response, kena_limit = ambil_batch(params)

    if kena_limit:
        berhenti = True
        break

    if response is None:
        continue

    for indeks, baris in enumerate(perlu):
        hasil = response_lokasi(response, indeks)

        if isinstance(hasil, dict) and "hourly" in hasil:
            proses_lokasi(baris, hasil)
        else:
            print(
                "   response tidak valid:",
                baris["nama_kabkota"]
            )

    terpakai += bobot
    simpan_kuota(terpakai)

    print(
        "   batch berhasil; estimasi kuota:",
        round(terpakai)
    )

    time.sleep(5)

print("\nEstimasi kuota setelah run:", round(terpakai))


daftar_harian = []
belum_selesai = []
lengkap = []

for _, baris in kabkota.iterrows():
    kode = str(baris["kode_kabkota"]).replace(".", "_")
    file_data = DIR_MENTAH / f"udara_{kode}.csv"

    if not file_data.exists():
        belum_selesai.append(baris["nama_kabkota"])
        continue

    frame = pd.read_csv(file_data)

    if frame.empty or "time" not in frame.columns:
        belum_selesai.append(baris["nama_kabkota"])
        continue

    daftar_harian.append(ke_harian(baris, frame))

    if sudah_mencakup(file_data, TANGGAL_AKHIR):
        lengkap.append(baris["nama_kabkota"])

print(
    "Kab/kota memiliki file udara:",
    len(daftar_harian),
    "dari",
    len(kabkota)
)
print(
    "Kab/kota lengkap sampai akhir periode:",
    len(lengkap),
    "dari",
    len(kabkota)
)
print(
    "Kab/kota belum memiliki file:",
    len(belum_selesai)
)

if daftar_harian:
    data_akhir = pd.concat(
        daftar_harian,
        ignore_index=True
    )

    output = (
        DIR_GABUNGAN
        / "airguard_harian_kualitas_udara_jawa.csv"
    )

    data_akhir.to_csv(output, index=False)

    print("Total baris:", len(data_akhir))
    print("Missing value:")
    print(data_akhir.isna().sum())
    print("Tersimpan di", output)
