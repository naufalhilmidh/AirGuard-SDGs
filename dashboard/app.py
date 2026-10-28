import urllib.parse

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (BATAS_TINGGI, CUACA, KATEGORI, KOTA, PALET_KOTA, PROV_DARI_KOTA, PROVINSI, URUTAN_KATEGORI,
                   WARNA_KATEGORI, WARNA_PREDIKSI, WARNA_PROVINSI, WARNA_UTAMA, WILAYAH, muat_data, nama_kategori)

st.set_page_config(page_title="AirGuard SDGs", layout="wide")

# ---------- Ilustrasi banner (SVG buatan sendiri: langit, kota berkabut, perbukitan, pepohonan) ----------
def _pohon(x, y, s, warna):
    return (f"<rect x='{x - 2 * s}' y='{y}' width='{4 * s}' height='{10 * s}' fill='#3B3A2E'/>"
            f"<path d='M{x - 14 * s} {y + 4 * s} L{x} {y - 34 * s} L{x + 14 * s} {y + 4 * s}Z' fill='{warna}'/>"
            f"<path d='M{x - 11 * s} {y - 14 * s} L{x} {y - 48 * s} L{x + 11 * s} {y - 14 * s}Z' fill='{warna}'/>")


def ilustrasi_uri(mode="hero"):
    if mode == "bar":
        pohon = "".join(_pohon(x, y, s, w) for x, y, s, w in
                        [(1090, 112, 0.55, "#2F6149"), (1130, 116, 0.7, "#27533F"), (1170, 111, 0.55, "#2F6149"),
                         (760, 118, 0.45, "#3A7254")])
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 130' preserveAspectRatio='xMaxYMax slice'>"
            "<rect width='1200' height='130' fill='#D6E8DC'/>"
            "<circle cx='1000' cy='38' r='34' fill='#F7DE8A' opacity='.35'/><circle cx='1000' cy='38' r='20' fill='#F7DE8A'/>"
            "<g fill='#FFFFFF' opacity='.85'><ellipse cx='820' cy='34' rx='46' ry='10'/><ellipse cx='850' cy='26' rx='28' ry='9'/>"
            "<ellipse cx='1120' cy='56' rx='40' ry='9'/></g>"
            "<path d='M0 96 Q200 74 420 92 T860 86 T1200 92 V130 H0Z' fill='#B9D4B1'/>"
            "<path d='M0 110 Q260 92 520 106 T1200 102 V130 H0Z' fill='#86B08A'/>"
            "<path d='M0 124 Q300 110 600 120 T1200 118 V130 H0Z' fill='#5E9470'/>"
            f"{pohon}</svg>"
        )
        return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)
    gedung = "".join(f"<rect x='{x}' y='{y}' width='{w}' height='{220 - y}'/>" for x, y, w in
                     [(830, 175, 22), (856, 150, 26), (886, 165, 20), (910, 140, 30), (944, 170, 22),
                      (970, 155, 26), (1000, 172, 20), (1024, 160, 24), (1052, 178, 22)])
    pohon = "".join(_pohon(x, y, s, w) for x, y, s, w in
                    [(1060, 300, 1.0, "#2F6149"), (1110, 306, 1.25, "#27533F"), (1165, 298, 1.0, "#2F6149"),
                     (700, 312, 0.8, "#3A7254")])
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 340' preserveAspectRatio='xMaxYMax slice'>"
        "<rect width='1200' height='340' fill='#D6E8DC'/>"
        "<circle cx='1100' cy='80' r='64' fill='#F7DE8A' opacity='.35'/><circle cx='1100' cy='80' r='40' fill='#F7DE8A'/>"
        "<g fill='#FFFFFF' opacity='.85'><ellipse cx='830' cy='62' rx='56' ry='15'/><ellipse cx='868' cy='50' rx='38' ry='13'/>"
        "<ellipse cx='1130' cy='150' rx='48' ry='12'/><ellipse cx='960' cy='112' rx='42' ry='11'/></g>"
        "<path d='M0 250 Q150 190 320 225 T640 215 T960 205 T1200 215 V340 H0Z' fill='#B9D4B1'/>"
        f"<g fill='#9DB8AD'>{gedung}</g>"
        "<rect x='780' y='140' width='420' height='84' fill='#EFE6B8' opacity='.30'/>"
        "<path d='M0 282 Q200 232 420 264 T860 252 T1200 264 V340 H0Z' fill='#86B08A'/>"
        "<path d='M0 312 Q260 272 520 300 T1200 292 V340 H0Z' fill='#5E9470'/>"
        f"{pohon}</svg>"
    )
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)


st.markdown(
    "<style>.st-key-hero{background-image:url(\"" + ilustrasi_uri("hero") + "\");}"
    ".st-key-topbar,.st-key-cta{background-image:url(\"" + ilustrasi_uri("bar") + "\");}</style>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
    .stApp {background: #EDF1E9;}
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp li, .stTabs button {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .block-container {padding-top: 4.5rem; padding-bottom: 4rem; max-width: 1280px;}
    [data-testid="stVerticalBlock"] {gap: 1.1rem;}
    [data-testid="stHeader"] {background: transparent;}

    /* sidebar hijau gelap */
    [data-testid="stSidebar"] {background: #1F4D3E !important;}
    [data-testid="stSidebar"] h2 {color: #FFFFFF !important; font-size: 1.05rem !important;}
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color: #D5E4D0 !important;}
    [data-testid="stSidebar"] [data-testid="stAlert"] {background: #F6EBC7 !important; border: none !important;}
    [data-testid="stSidebar"] [data-testid="stAlert"] p {color: #4A3A00 !important;}
    .brand {display: flex; gap: 12px; align-items: center; padding: 6px 0 16px; margin-bottom: 8px;
        border-bottom: 1px solid rgba(255,255,255,.18);}
    .brand .lg {width: 40px; height: 40px; border-radius: 12px; background: #A8C66C; color: #1F4D3E;
        display: flex; align-items: center; justify-content: center;}
    .brand .lg svg {width: 22px; height: 22px;}
    .brand .bn {color: #FFFFFF; font-weight: 600; font-size: 1.05rem;}
    .brand .bs {color: #BFD3BA; font-size: .8rem;}

    /* tab: kotak, memenuhi lebar, berubah warna saat aktif */
    [data-testid="stTabs"] [role="tablist"] {gap: 10px !important; overflow: visible !important; margin-bottom: 1.2rem !important;}
    [data-testid="stTabs"] [role="tablist"]::after {display: none !important;}
    [data-testid="stTab"], button[data-baseweb="tab"] {
        flex: 1 1 0 !important; justify-content: center !important; height: auto !important; margin: 0 !important;
        padding: .8rem 1rem !important; background: #FBFCF8 !important; border: 1px solid #DDE5D6 !important;
        border-radius: 12px !important; color: #17302A !important;
    }
    [data-testid="stTab"] p, button[data-baseweb="tab"] p {font-size: 1rem !important; font-weight: 500 !important; color: #17302A !important;}
    [data-testid="stTab"]:hover, button[data-baseweb="tab"]:hover {background: #E3ECDD !important;}
    [data-testid="stTab"][data-selected], [data-testid="stTab"][aria-selected="true"],
    button[data-baseweb="tab"][aria-selected="true"] {background: #1F4D3E !important; border-color: #1F4D3E !important;}
    [data-testid="stTab"][data-selected] p, [data-testid="stTab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] p {color: #FFFFFF !important; font-weight: 600 !important;}
    [data-testid="stTab"] .react-aria-SelectionIndicator, div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {display: none !important;}

    .stApp h3 {font-size: 1.1rem !important; font-weight: 600 !important; padding: .4rem 0 .1rem !important; color: #17302A;}
    [class*="st-key-card_"] h3 {padding-top: 0 !important;}

    /* kartu */
    [class*="st-key-card_"], .kartu {
        background: #FBFCF8; border: 1px solid #DDE5D6; border-radius: 16px; padding: 18px 20px;
        box-shadow: 0 1px 2px rgba(23,48,42,.05), 0 8px 24px rgba(23,48,42,.05);
    }
    .kartu.flat {border: none; box-shadow: none; padding: 0; background: none;}
    .grid {display: grid; gap: 16px; align-items: stretch; margin-bottom: 1rem;}
    .g3 {grid-template-columns: repeat(3, minmax(0, 1fr));}
    .g4 {grid-template-columns: repeat(4, minmax(0, 1fr));}
    .jud {font-weight: 600; font-size: .95rem; margin-bottom: 6px; color: #17302A;}
    .isi {font-size: .9rem; line-height: 1.55; color: #3D5048;}
    .stat .atas {display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;}
    .stat .lab {font-size: .82rem; color: #5A6B66;}
    .stat .ic {width: 36px; height: 36px; border-radius: 11px; display: flex; align-items: center; justify-content: center;
        color: #1F4D3E; flex: none;}
    .stat .ic svg {width: 19px; height: 19px;}
    .stat .val {font-size: 1.75rem; font-weight: 600; margin: 6px 0 2px; color: #17302A;}
    .stat .ket {font-size: .82rem; color: #5A6B66;}
    .intro {background: #E3ECDD; border-radius: 14px; padding: 14px 18px; font-size: .93rem; line-height: 1.6; color: #17302A;}
    @media (max-width: 900px) {.g3, .g4 {grid-template-columns: repeat(2, minmax(0, 1fr));}}

    /* banner berilustrasi (landing, bagian atas dashboard, ajakan penutup) */
    .st-key-hero, .st-key-topbar, .st-key-cta {
        background-color: #D6E8DC; background-size: cover; background-position: right bottom;
        background-repeat: no-repeat; border-radius: 20px; overflow: hidden;
        box-shadow: 0 1px 2px rgba(23,48,42,.06), 0 10px 28px rgba(23,48,42,.08);
    }
    .st-key-hero {padding: 48px 52px; min-height: 340px;}
    .st-key-cta {padding: 36px 52px; min-height: 200px;}
    .st-key-topbar {padding: 22px 28px; min-height: 130px;}
    .st-key-hero .eyebrow {font-size: .78rem; font-weight: 600; letter-spacing: .08em; color: #1F6F54 !important;}
    .st-key-hero h1 {font-size: 2.9rem; margin: .4rem 0 .8rem; padding: 0; color: #17302A !important;}
    .st-key-hero .lead {font-size: 1.1rem; line-height: 1.65; max-width: 520px; color: #2B463D !important; margin: 0 0 18px;}
    .glass {display: inline-block; font-size: .85rem; color: #17302A !important; background: rgba(255,255,255,.62);
        border: 1px solid rgba(255,255,255,.85); border-radius: 99px; padding: 6px 14px; margin: 0 8px 8px 0;
        backdrop-filter: blur(6px);}
    .st-key-cta .ctaT {font-size: 1.5rem; font-weight: 600; color: #17302A !important;}
    .st-key-cta .ctaS {font-size: 1rem; color: #2B463D !important; margin: 4px 0 8px; max-width: 560px;}
    .st-key-masuk_atas button, .st-key-masuk_bawah button {
        background: #1F4D3E !important; border: none !important; border-radius: 12px !important;
        padding: .7rem 1.8rem !important; min-height: 3rem;
    }
    .st-key-masuk_atas button:hover, .st-key-masuk_bawah button:hover {background: #2B6A55 !important;}
    .st-key-masuk_atas button p, .st-key-masuk_bawah button p {color: #FFFFFF !important; font-weight: 600 !important; font-size: 1rem !important;}
    .st-key-kembali button {background: rgba(255,255,255,.85) !important; border: 1px solid #DDE5D6 !important; border-radius: 12px !important;}
    .st-key-kembali button:hover {background: #FFFFFF !important;}
    .st-key-kembali button p {color: #17302A !important; font-weight: 500 !important;}
    .judul-dash {font-size: 1.4rem; font-weight: 600; color: #17302A;}
    .sub-dash {font-size: .9rem; color: #2B463D;}
    .pill {display: inline-block; font-size: .85rem; font-weight: 600; padding: 4px 12px; border-radius: 99px;}
    .besar {font-size: 2.6rem; font-weight: 600; line-height: 1.1; margin: 6px 0 8px; color: #17302A;}
    .chipsdg {display: inline-block; font-size: .75rem; font-weight: 600; padding: 3px 10px; border-radius: 6px;
        background: #1F4D3E; color: #E9F2C8; margin-bottom: 10px;}
    .no {display: inline-flex; width: 32px; height: 32px; border-radius: 50%; background: #1F4D3E; color: #FFFFFF;
        font-weight: 600; align-items: center; justify-content: center; margin-bottom: 10px;}

    /* legenda kategori */
    .kat {display: flex; align-items: center; gap: 10px; padding: 8px 0; border-top: 1px solid #E6ECE0; font-size: .9rem;}
    .kat:first-of-type {border-top: none;}
    .dot {width: 12px; height: 12px; border-radius: 50%; flex: none;}
    .kat .rg {margin-left: auto; color: #5A6B66; white-space: nowrap;}
    </style>
    """,
    unsafe_allow_html=True,
)

TEKS_KATEGORI = {"Baik": "#14231F", "Sedang": "#14231F", "Tidak sehat": "#14231F",
                 "Sangat tidak sehat": "#FFFFFF", "Berbahaya": "#FFFFFF"}
SARAN = {
    "Baik": "Kualitas udara baik. Aktivitas di luar ruangan aman dilakukan.",
    "Sedang": "Kelompok sensitif (anak, lansia, penderita asma) sebaiknya mengurangi aktivitas berat di luar ruangan.",
    "Tidak sehat": "Kurangi aktivitas berat di luar ruangan. Pertimbangkan memakai masker bila harus keluar.",
    "Sangat tidak sehat": "Hindari aktivitas di luar ruangan, terutama untuk kelompok sensitif.",
    "Berbahaya": "Hindari aktivitas di luar ruangan dan tetap berada di dalam ruangan.",
}
_SV = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
       'stroke-linecap="round" stroke-linejoin="round">{}</svg>')
IKON = {
    "pin": _SV.format('<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>'),
    "angin": _SV.format('<path d="M3 8h11a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h8"/>'),
    "tren": _SV.format('<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>'),
    "awas": _SV.format('<path d="M12 3l10 18H2L12 3zM12 10v5M12 18v.5"/>'),
    "daun": _SV.format('<path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14M5 19c2-4 5-7 9-9"/>'),
}


def kartu(judul, isi, atas="", kelas=""):
    return f'<div class="kartu {kelas}">{atas}<div class="jud">{judul}</div><div class="isi">{isi}</div></div>'


def stat(label, nilai, ket, ikon, warna):
    return (f'<div class="kartu stat"><div class="atas"><div class="lab">{label}</div>'
            f'<div class="ic" style="background:{warna}">{IKON[ikon]}</div></div>'
            f'<div class="val">{nilai}</div><div class="ket">{ket}</div></div>')


def grid(kelas, *isi):
    st.markdown(f'<div class="grid {kelas}">{"".join(isi)}</div>', unsafe_allow_html=True)


def intro(teks):
    st.markdown(f'<div class="intro">{teks}</div>', unsafe_allow_html=True)


def kotak(nama):
    return st.container(key=f"card_{nama}")


def pakai_tema(fig, tinggi=380):
    fig.update_layout(
        template="simple_white", height=tinggi, margin=dict(l=10, r=10, t=20, b=10),
        font=dict(family="IBM Plex Sans, sans-serif", size=13, color="#17302A"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.3, title=None),
    )
    return fig


def masuk():
    st.session_state["halaman"] = "dashboard"


def kembali():
    st.session_state["halaman"] = "landing"


pred, pre, metrik, fitur, memakai_contoh, tak_cocok = muat_data()
tgl_aktual = pred.loc[pred["pm2_5_aktual"].notna(), "tanggal_prediksi"]
_ada = set(pred["kota"].unique())  # berlaku untuk kolom teks maupun kategori
semua_kota = [k for k in KOTA if k in _ada]
TIPE_DARI_KOTA = dict(zip(WILAYAH["kota"], WILAYAH["tipe"]))
PENDUDUK = dict(zip(WILAYAH["kota"], WILAYAH["penduduk"]))


def daerah_awal(daftar):
    """Indeks daerah bawaan: kota berpenduduk terbanyak dalam daftar (kalau tidak ada kota, kabupaten terbesar)."""
    kota_saja = [k for k in daftar if TIPE_DARI_KOTA[k] == "Kota"] or list(daftar)
    return list(daftar).index(max(kota_saja, key=lambda k: PENDUDUK[k]))


@st.fragment
def cek_kondisi(terakhir, besok):
    # fragment: ganti provinsi/kota hanya menghitung ulang bagian ini, bukan seluruh beranda
    st.subheader("Cek kondisi daerahmu")
    p1, p2, _ = st.columns([1, 1.3, 2])
    prov = p1.selectbox("Provinsi", PROVINSI, key="prov_beranda")
    opsi = [k for k in semua_kota if PROV_DARI_KOTA[k] == prov]
    awal = next((i for i, k in enumerate(opsi) if TIPE_DARI_KOTA[k] == "Kota"), 0)
    kota = p2.selectbox("Kabupaten/kota", opsi, index=awal, key=f"kota_beranda_{prov}", help="Ketik untuk mencari nama.")
    d = pred[pred["kota"] == kota].sort_values("tanggal_prediksi")
    baris_besok = d[d["tanggal_prediksi"] == besok]
    baris_ini = d[d["tanggal_prediksi"] == terakhir]

    kiri, kanan = st.columns([1, 1.4], gap="large")
    with kiri:
        if baris_besok.empty or baris_ini.empty:
            st.info("Belum ada prediksi untuk kota ini.")
        else:
            nilai = float(baris_besok["pm2_5_prediksi"].iloc[0])
            ini = float(baris_ini["pm2_5_aktual"].iloc[0])
            kat = nama_kategori(nilai)
            selisih = nilai - ini
            arah = "Naik" if selisih > 0 else "Turun"
            st.markdown(
                f'<div class="kartu"><div style="font-size:.85rem;color:#5A6B66">'
                f'Prediksi PM2.5 {kota}, {besok:%d %b %Y}</div>'
                f'<div class="besar">{nilai:.1f} <span style="font-size:1rem;font-weight:500;color:#5A6B66">µg/m³</span></div>'
                f'<span class="pill" style="background:{WARNA_KATEGORI[kat]};color:{TEKS_KATEGORI[kat]}">{kat}</span>'
                f'<div class="isi" style="margin-top:14px">{arah} {abs(selisih):.1f} dari kondisi terakhir ({ini:.1f}).</div>'
                f'<div class="isi" style="margin-top:8px">{SARAN[kat]}</div>'
                f'<div class="isi" style="margin-top:10px;font-size:.8rem;color:#5A6B66">'
                f'Ringkasan umum berdasarkan kategori ISPU, bukan saran medis.</div></div>',
                unsafe_allow_html=True,
            )
    with kanan:
        with kotak("cek"):
            t = d.tail(31)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=t["tanggal_prediksi"], y=t["pm2_5_aktual"], name="Aktual",
                                     line=dict(color=WARNA_UTAMA, width=2)))
            fig.add_trace(go.Scatter(x=t["tanggal_prediksi"], y=t["pm2_5_prediksi"], name="Prediksi",
                                     line=dict(color=WARNA_PREDIKSI, width=1.8, dash="dash")))
            fig.update_yaxes(title="PM2.5 (µg/m³)")
            st.plotly_chart(pakai_tema(fig, 270))
            st.caption(f"30 hari terakhir di {kota}. Titik oranye paling kanan adalah prediksi untuk besok.")


# ====================== LANDING PAGE ======================
def landing():
    terakhir = tgl_aktual.max()
    besok = terakhir + pd.Timedelta(days=1)

    with st.container(key="hero"):
        st.markdown(
            '<div class="eyebrow">SDG 3 · SDG 11 · SDG 13</div>'
            '<h1>AirGuard SDGs</h1>'
            '<p class="lead">Prediksi dan pemetaan risiko PM2.5 hari berikutnya untuk kabupaten dan kota di Pulau Jawa. '
            'Data kualitas udara dan cuaca harian dari Open-Meteo dipakai untuk memprediksi konsentrasi PM2.5 esok hari, '
            'lalu ditampilkan dalam bentuk peta, tren, dan kategori risiko.</p>'
            f'<span class="glass">{len(semua_kota)} kabupaten/kota, {len(PROVINSI)} provinsi</span>'
            f'<span class="glass">Data aktual sampai {terakhir:%d %b %Y}</span>'
            f'<span class="glass">Prediksi untuk {besok:%d %b %Y}</span>',
            unsafe_allow_html=True,
        )
        st.button("Masuk ke Dashboard →", key="masuk_atas", on_click=masuk)

    cek_kondisi(terakhir, besok)

    st.subheader("Prediksi besok per provinsi")
    st.caption("Rata-rata prediksi dari semua kabupaten/kota di provinsi itu. Angka rata-rata bisa menyembunyikan "
               "daerah yang tinggi, jadi jumlah daerah berisiko tinggi ditampilkan terpisah.")
    pb = pred[pred["tanggal_prediksi"] == besok]
    kartu_prov = []
    for p in PROVINSI:
        x = pb[pb["provinsi"] == p]
        if x.empty:
            continue
        rata = float(x["pm2_5_prediksi"].mean())
        kat_p = nama_kategori(rata)
        tinggi = int((x["pm2_5_prediksi"] > BATAS_TINGGI).sum())
        kartu_prov.append(
            f'<div class="kartu"><div class="jud">{p}</div>'
            f'<div class="besar" style="font-size:1.9rem">{rata:.1f} <span style="font-size:.9rem;font-weight:500;color:#5A6B66">µg/m³</span></div>'
            f'<span class="pill" style="background:{WARNA_KATEGORI[kat_p]};color:{TEKS_KATEGORI[kat_p]}">{kat_p}</span>'
            f'<div class="isi" style="margin-top:10px">{tinggi} dari {len(x)} kabupaten/kota berisiko tinggi</div></div>')
    grid("g3", *kartu_prov)

    st.subheader("Kaitan dengan SDGs")
    chip = lambda t: f'<span class="chipsdg">{t}</span><br>'
    grid(
        "g3",
        kartu("Kehidupan sehat dan sejahtera",
              "PM2.5 adalah partikel berdiameter kurang dari 2,5 mikrometer yang mudah terhirup. "
              "Prediksi membantu masyarakat menyiapkan diri.", chip("SDG 3")),
        kartu("Kota dan permukiman berkelanjutan",
              "Peta dan peringkat kabupaten/kota maupun provinsi menunjukkan wilayah yang paling perlu mendapat perhatian.", chip("SDG 11")),
        kartu("Penanganan perubahan iklim",
              "Pola polusi dibaca bersama kondisi cuaca untuk memahami kapan polusi meningkat.", chip("SDG 13")),
    )

    st.subheader("Yang bisa kamu lihat di dashboard")
    grid(
        "g4",
        kartu("Ringkasan", "Kondisi terbaru, prediksi besok, peta Pulau Jawa, dan peringkat per kabupaten/kota atau provinsi."),
        kartu("Tren & Prediksi", "PM2.5 aktual dibandingkan prediksi, plus daftar episode polusi tinggi."),
        kartu("Cuaca", "Pola PM2.5 yang berkaitan dengan suhu, kelembapan, hujan, dan angin."),
        kartu("Model", "Seberapa akurat prediksi dibanding tebakan sederhana, dan fitur yang paling dipakai model."),
    )

    with st.container(key="cta"):
        st.markdown('<div class="ctaT">Siap melihat datanya?</div>'
                    '<div class="ctaS">Buka dashboard untuk peta risiko, tren, pengaruh cuaca, dan performa model.</div>',
                    unsafe_allow_html=True)
        st.button("Masuk ke Dashboard →", key="masuk_bawah", on_click=masuk)
    st.caption("Proyek kelompok mata kuliah SDGs, PENS. Sumber data: Open-Meteo.")


# ====================== HALAMAN DASHBOARD ======================
def legenda_kategori():
    baris, bawah = [], 0.0
    for batas, nama, warna in KATEGORI:
        rentang_teks = f"&gt; {bawah - 0.1:.1f}" if batas == float("inf") else f"{bawah:.1f} – {batas:.1f}"
        baris.append(f'<div class="kat"><span class="dot" style="background:{warna}"></span>'
                     f'<span>{nama}</span><span class="rg">{rentang_teks}</span></div>')
        bawah = batas + 0.1
    return (f'<div class="kartu flat">'
            f'<div class="isi" style="margin-bottom:6px">PM2.5 rata-rata 24 jam (µg/m³), mengikuti ISPU.</div>'
            f'{"".join(baris)}</div>')


def ringkasan():
    p = pred_f
    terakhir = p.loc[p["pm2_5_aktual"].notna(), "tanggal_prediksi"].max()
    besok = terakhir + pd.Timedelta(days=1)

    hari_ini = p[p["tanggal_prediksi"] == terakhir].set_index("kota")["pm2_5_aktual"]
    prediksi = p[p["tanggal_prediksi"] == besok].set_index("kota")["pm2_5_prediksi"]
    rata = p[p["tanggal_prediksi"].between(t0, t1)].groupby("kota")["pm2_5_aktual"].mean()

    tabel = pd.DataFrame({"PM2.5 hari ini": hari_ini, "Prediksi besok": prediksi, "Rata-rata periode": rata})
    tabel = tabel.dropna(subset=["PM2.5 hari ini", "Prediksi besok"]).reset_index()
    tabel["kota"] = tabel["kota"].astype(str)
    tabel["Provinsi"] = tabel["kota"].map(PROV_DARI_KOTA)
    tabel["lat"] = tabel["kota"].map(lambda k: KOTA[k][0])
    tabel["lon"] = tabel["kota"].map(lambda k: KOTA[k][1])

    if tabel.empty:
        st.info("Belum ada data prediksi untuk wilayah yang dipilih.")
        return

    intro("<b>Halaman ini menjawab:</b> daerah mana yang paling berisiko besok? "
          "Angka <i>hari ini</i> adalah data aktual terakhir, sedangkan angka <i>besok</i> adalah hasil prediksi model. "
          "Kamu bisa melihatnya per kabupaten/kota atau dirangkum per provinsi.")

    tingkat = st.radio("Tampilkan per", ["Kabupaten/kota", "Provinsi"], horizontal=True, key="tingkat_ringkasan")
    per_prov = tingkat == "Provinsi"

    if per_prov:
        g = tabel.groupby("Provinsi")
        t = g.agg(**{
            "PM2.5 hari ini": ("PM2.5 hari ini", "mean"), "Prediksi besok": ("Prediksi besok", "mean"),
            "Rata-rata periode": ("Rata-rata periode", "mean"), "lat": ("lat", "mean"), "lon": ("lon", "mean"),
            "Jumlah wilayah": ("kota", "size"),
            "Berisiko tinggi besok": ("Prediksi besok", lambda x: int((x > BATAS_TINGGI).sum())),
        }).reset_index().rename(columns={"Provinsi": "Wilayah"})
    else:
        t = tabel.rename(columns={"kota": "Wilayah"})
    t["Perubahan"] = t["Prediksi besok"] - t["PM2.5 hari ini"]
    t["Kategori besok"] = t["Prediksi besok"].map(nama_kategori)

    tinggi_h = t.loc[t["PM2.5 hari ini"].idxmax()]
    tinggi_b = t.loc[t["Prediksi besok"].idxmax()]
    kota_tinggi = tabel.loc[tabel["Prediksi besok"] > BATAS_TINGGI, "kota"].tolist()
    ket_tinggi = "Tidak ada"
    if kota_tinggi:
        ket_tinggi = ", ".join(kota_tinggi[:2]) + (f" dan {len(kota_tinggi) - 2} lainnya" if len(kota_tinggi) > 2 else "")

    st.caption(f"Data aktual terakhir: {terakhir:%d %b %Y}. Prediksi untuk {besok:%d %b %Y}."
               + (" Angka provinsi adalah rata-rata sederhana dari kabupaten/kota di dalamnya." if per_prov else ""))
    grid(
        "g4",
        stat("PM2.5 hari ini tertinggi", f"{tinggi_h['PM2.5 hari ini']:.1f} µg/m³", f"{tinggi_h['Wilayah']}", "angin", "#DCEBD8"),
        stat("Prediksi besok tertinggi", f"{tinggi_b['Prediksi besok']:.1f} µg/m³", f"{tinggi_b['Wilayah']}", "tren", "#E8F0C9"),
        stat("Berisiko tinggi besok", f"{len(kota_tinggi)} dari {len(tabel)}", ket_tinggi, "awas", "#F8E7C4"),
        stat("Wilayah dipantau", f"{len(tabel)}", f"kabupaten/kota di {tabel['Provinsi'].nunique()} provinsi", "pin", "#D5E8E4"),
    )

    kiri, kanan = st.columns([3, 1.4], gap="large")
    with kiri:
        with kotak("peta"):
            st.subheader("Peta risiko besok")
            st.caption("Setiap titik adalah satu " + ("provinsi (di titik tengah kabupaten/kota-nya)" if per_prov else "kabupaten/kota")
                       + ". Warnanya menunjukkan kategori risiko dari PM2.5 yang diprediksi untuk besok, "
                       "bukan kondisi hari ini. Arahkan kursor ke titik untuk melihat angkanya.")
            hover = {"Prediksi besok": ":.1f", "Kategori besok": True, "lat": False, "lon": False}
            hover["Berisiko tinggi besok" if per_prov else "Provinsi"] = True
            fig = px.scatter_map(
                t, lat="lat", lon="lon", color="Kategori besok", text="Wilayah" if len(t) <= 12 else None,
                hover_name="Wilayah", hover_data=hover,
                color_discrete_map=WARNA_KATEGORI, category_orders={"Kategori besok": URUTAN_KATEGORI},
                zoom=5.2, center={"lat": -7.4, "lon": 109.8}, map_style="carto-positron",
            )
            fig.update_traces(marker=dict(size=22 if per_prov else 11), textposition="top center", textfont=dict(size=12))
            fig.update_layout(height=440, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
            st.plotly_chart(fig)
    with kanan:
        with kotak("legenda"):
            st.subheader("Keterangan warna")
            st.markdown(legenda_kategori(), unsafe_allow_html=True)

    with kotak("peringkat"):
        st.subheader("Peringkat " + ("provinsi" if per_prov else "kabupaten/kota"))
        f1, f2, _ = st.columns([1, 1, 2])
        urut = f1.selectbox("Urutkan berdasarkan", ["Prediksi besok", "PM2.5 hari ini", "Rata-rata periode"])
        if per_prov:
            jumlah = len(t)
        else:
            pilihan = f2.selectbox("Tampilkan", ["10 teratas", "20 teratas", "Semua"])
            jumlah = len(t) if pilihan == "Semua" else int(pilihan.split()[0])
        kolom = ["Wilayah", "Jumlah wilayah", "Berisiko tinggi besok"] if per_prov else ["Wilayah", "Provinsi"]
        kolom += ["PM2.5 hari ini", "Prediksi besok", "Perubahan", "Rata-rata periode", "Kategori besok"]
        tampil = t.sort_values(urut, ascending=False).head(jumlah)[kolom].rename(
            columns={"Wilayah": "Provinsi" if per_prov else "Kabupaten/kota", "Jumlah wilayah": "Jumlah kab/kota"})
        st.dataframe(
            tampil, hide_index=True, height=min(38 * (len(tampil) + 1) + 3, 440),
            column_config={
                "PM2.5 hari ini": st.column_config.NumberColumn(format="%.1f"),
                "Prediksi besok": st.column_config.NumberColumn(format="%.1f"),
                "Perubahan": st.column_config.NumberColumn(format="%+.1f"),
                "Rata-rata periode": st.column_config.NumberColumn(format="%.1f"),
            },
        )
        st.caption("Satuan PM2.5: µg/m³. Perubahan = prediksi besok dikurangi PM2.5 hari ini. "
                   "Rata-rata periode dihitung dari rentang tanggal di sidebar. "
                   "Tabel bisa dicari lewat ikon kaca pembesar di pojok kanan atas tabel.")


def episode(d, ambang):
    f = d[d["pm2_5_aktual"] > ambang].sort_values("tanggal_prediksi")
    if f.empty:
        return pd.DataFrame()
    grup = f["tanggal_prediksi"].diff().dt.days.ne(1).cumsum()
    e = f.groupby(grup).agg(Mulai=("tanggal_prediksi", "min"), Selesai=("tanggal_prediksi", "max"),
                            Puncak=("pm2_5_aktual", "max")).reset_index(drop=True)
    e["Durasi (hari)"] = (e["Selesai"] - e["Mulai"]).dt.days + 1
    e["Mulai"] = e["Mulai"].dt.strftime("%d %b %Y")
    e["Selesai"] = e["Selesai"].dt.strftime("%d %b %Y")
    return e.sort_values("Puncak", ascending=False)


def tren():
    intro("<b>Halaman ini menjawab:</b> kapan polusi meningkat, dan seberapa dekat prediksi model dengan kenyataan?")

    f0, f1, f2, _ = st.columns([1.7, 1.5, 1.1, 0.4], gap="large")
    level = f0.radio("Lihat", ["Kabupaten/kota", "Provinsi"], horizontal=True, key="level_tren")
    if level == "Provinsi":
        opsi = [p for p in PROVINSI if p in {PROV_DARI_KOTA[k] for k in pilih_kota}]
        kota = f1.selectbox("Provinsi", opsi)
        d = (pred_f[pred_f["provinsi"] == kota]
             .groupby("tanggal_prediksi", as_index=False)[["pm2_5_aktual", "pm2_5_prediksi"]].mean())
        d["error"] = d["pm2_5_prediksi"] - d["pm2_5_aktual"]
    else:
        kota = f1.selectbox("Kabupaten/kota", pilih_kota, index=daerah_awal(pilih_kota), help="Ketik untuk mencari nama.")
        d = pred[pred["kota"] == kota]
    ambang = f2.number_input("Ambang polusi tinggi (µg/m³)", value=float(BATAS_TINGGI), step=1.0, format="%.1f",
                             help="Bawaan: batas atas kategori Sedang pada ISPU.")

    d = d.sort_values("tanggal_prediksi").copy()
    d["Rata-rata 7 hari"] = d["pm2_5_aktual"].rolling(7, min_periods=1).mean()
    d = d[(d["tanggal_prediksi"] >= t0) & ((d["tanggal_prediksi"] <= t1) | d["pm2_5_aktual"].isna())]

    with kotak("tren"):
        st.subheader(f"PM2.5 aktual dan prediksi, {kota}" + (" (rata-rata kab/kota)" if level == "Provinsi" else ""))
        st.caption("Garis hijau tua adalah nilai sebenarnya, garis oranye putus-putus adalah prediksi model, "
                   "dan garis abu-abu adalah rata-rata 7 hari yang menghaluskan naik-turun harian. "
                   "Garis merah putus-putus adalah ambang polusi tinggi. Titik oranye paling kanan adalah prediksi besok.")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d["tanggal_prediksi"], y=d["pm2_5_aktual"], name="Aktual",
                                 line=dict(color=WARNA_UTAMA, width=2)))
        fig.add_trace(go.Scatter(x=d["tanggal_prediksi"], y=d["pm2_5_prediksi"], name="Prediksi",
                                 line=dict(color=WARNA_PREDIKSI, width=1.8, dash="dash")))
        fig.add_trace(go.Scatter(x=d["tanggal_prediksi"], y=d["Rata-rata 7 hari"], name="Rata-rata 7 hari",
                                 line=dict(color="#8A9A95", width=1.5, dash="dot")))
        fig.add_trace(go.Scatter(x=[d["tanggal_prediksi"].min(), d["tanggal_prediksi"].max()], y=[ambang, ambang],
                                 name=f"Ambang ({ambang:.1f})", mode="lines",
                                 line=dict(color="#A23B3B", width=1, dash="longdash")))
        fig.update_yaxes(title="PM2.5 (µg/m³)")
        st.plotly_chart(pakai_tema(fig, 380))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("error"):
            st.subheader("Selisih prediksi dan aktual")
            st.caption("Di atas nol berarti model memprediksi terlalu tinggi, di bawah nol terlalu rendah. "
                       "Makin dekat ke nol, makin akurat.")
            e = d.dropna(subset=["pm2_5_aktual"])
            fig2 = go.Figure(go.Scatter(x=e["tanggal_prediksi"], y=e["error"], mode="lines", fill="tozeroy",
                                        line=dict(color=WARNA_UTAMA, width=1), fillcolor="rgba(15,92,85,0.25)",
                                        name="Selisih"))
            fig2.update_yaxes(title="Prediksi - aktual (µg/m³)", zeroline=True, zerolinecolor="#8A9A95")
            st.plotly_chart(pakai_tema(fig2, 300))
    with kanan:
        with kotak("episode"):
            st.subheader("Episode polusi tinggi")
            st.caption("Periode hari-hari berturut-turut ketika PM2.5 aktual melewati ambang. "
                       "Puncak adalah nilai tertinggi dalam periode itu.")
            ep = episode(d, ambang)
            if ep.empty:
                st.write("Tidak ada hari di atas ambang pada rentang ini.")
            else:
                st.dataframe(ep, hide_index=True, height=300,
                             column_config={"Puncak": st.column_config.NumberColumn(format="%.1f")})


@st.cache_data(show_spinner=False, max_entries=48)
def hitung_cuaca(daftar_kota, awal, akhir, grup):
    """Agregasi berat untuk tab Cuaca. Di-cache per kombinasi filter supaya tidak dihitung ulang."""
    d = pre[pre["kota"].isin(daftar_kota) & pre["tanggal"].between(awal, akhir)]
    harian = d.groupby([grup, "tanggal"], as_index=False, observed=True)[["pm2_5", *CUACA]].mean()
    korelasi = pd.DataFrame({
        k: g[list(CUACA)].corrwith(g["pm2_5"]) for k, g in harian.groupby(grup, observed=True)
    }).T.rename(columns=CUACA)
    bulanan = d.assign(bulan=d["tanggal"].dt.month).groupby(["bulan", grup], as_index=False, observed=True)["pm2_5"].mean()
    contoh = d.sample(min(len(d), 1500), random_state=0)[["kota", "provinsi", "pm2_5", *CUACA]].copy()
    contoh["kota"] = contoh["kota"].astype(str)
    contoh["provinsi"] = contoh["provinsi"].astype(str)
    bulanan[grup] = bulanan[grup].astype(str)
    korelasi.index = korelasi.index.astype(str)
    return korelasi, bulanan, contoh


def cuaca():
    intro("<b>Halaman ini menjawab:</b> apakah PM2.5 cenderung naik atau turun bersamaan dengan kondisi cuaca tertentu, "
          "seperti suhu, kelembapan, hujan, dan angin? Hubungan yang terlihat adalah <i>pola yang berkaitan</i>, "
          "bukan bukti sebab-akibat.")

    if len(pilih_kota) <= 12:
        grup_nama = st.radio("Kelompokkan per", ["Provinsi", "Kabupaten/kota"], horizontal=True, key="grup_cuaca")
    else:
        grup_nama = "Provinsi"
        st.caption("Dikelompokkan per provinsi. Pilih 12 kabupaten/kota atau kurang di sidebar kalau ingin melihat per daerah.")
    grup = "provinsi" if grup_nama == "Provinsi" else "kota"
    korelasi, bulanan, contoh = hitung_cuaca(tuple(pilih_kota), t0, t1, grup)
    warna = WARNA_PROVINSI if grup == "provinsi" else dict(zip(sorted(contoh["kota"].unique()), PALET_KOTA * 2))

    with kotak("korelasi"):
        st.subheader("Korelasi PM2.5 dengan variabel cuaca")
        st.caption("Angka (r) berkisar dari -1 sampai +1. Mendekati +1 (merah): PM2.5 cenderung naik saat variabel itu naik. "
                   "Mendekati -1 (biru): PM2.5 cenderung turun saat variabel itu naik. "
                   "Mendekati 0: hampir tidak ada pola."
                   + (" Tiap baris memakai rata-rata harian semua kabupaten/kota di provinsi itu." if grup == "provinsi" else ""))
        fig = px.imshow(korelasi, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
        fig.update_layout(coloraxis_colorbar=dict(title="r", thickness=12))
        fig.update_xaxes(side="top")
        st.plotly_chart(pakai_tema(fig, 130 + 52 * len(korelasi)))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("sebar"):
            st.subheader("PM2.5 dan satu variabel cuaca")
            st.caption("Setiap titik adalah satu hari di satu kabupaten/kota. Kalau sebaran titik naik ke kanan, PM2.5 cenderung naik "
                       "bersama variabel yang dipilih. Kalau turun ke kanan, sebaliknya.")
            var = st.selectbox("Variabel cuaca", list(CUACA), format_func=CUACA.get)
            fig2 = px.scatter(contoh, x=var, y="pm2_5", color=grup, opacity=0.55, color_discrete_map=warna,
                              labels={var: CUACA[var], "pm2_5": "PM2.5 (µg/m³)", grup: grup_nama})
            st.plotly_chart(pakai_tema(fig2, 340))
    with kanan:
        with kotak("bulanan"):
            st.subheader("Rata-rata PM2.5 per bulan")
            st.caption("Bulan dengan nilai tinggi menunjukkan musim polusi pada data ini. "
                       "Berguna untuk melihat pola musiman tiap " + grup_nama.lower() + ".")
            st.markdown("<div style='height:4.6rem'></div>", unsafe_allow_html=True)
            fig3 = px.line(bulanan, x="bulan", y="pm2_5", color=grup, markers=True, color_discrete_map=warna,
                           labels={"bulan": "Bulan", "pm2_5": "PM2.5 (µg/m³)", grup: grup_nama})
            fig3.update_xaxes(tickmode="array", tickvals=list(range(1, 13)),
                              ticktext=["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"])
            st.plotly_chart(pakai_tema(fig3, 340))


@st.cache_data(show_spinner=False, max_entries=48)
def contoh_model(daftar_kota):
    e = pred[pred["kota"].isin(daftar_kota)].dropna(subset=["pm2_5_aktual"])
    e = e.sample(min(len(e), 1500), random_state=0)[["kota", "provinsi", "pm2_5_aktual", "pm2_5_prediksi"]].copy()
    e["provinsi"] = e["provinsi"].astype(str)
    return e


def model():
    intro("<b>Halaman ini menjawab:</b> seberapa bisa dipercaya prediksi AirGuard? "
          "Model machine learning dibandingkan dengan tebakan sederhana (baseline). "
          "Model hanya dianggap berguna jika konsisten lebih baik dari baseline.")

    with st.expander("Arti istilah di halaman ini", expanded=True):
        st.markdown(
            "- **Baseline**: tebakan sederhana sebagai pembanding. *Persistence*: besok dianggap sama dengan hari ini. "
            "*Rata-rata 7 hari*: besok dianggap sama dengan rata-rata 7 hari terakhir.\n"
            "- **MAE**: rata-rata selisih antara prediksi dan kenyataan, dalam µg/m³. "
            "MAE 4,8 berarti prediksi rata-rata meleset sekitar 4,8. Makin kecil makin baik. Ini metrik utama.\n"
            "- **RMSE**: mirip MAE, tetapi lebih menghukum kesalahan yang besar. Makin kecil makin baik.\n"
            "- **R²**: seberapa besar naik-turunnya PM2.5 yang bisa dijelaskan model, dari 0 sampai 1. "
            "Makin dekat 1 makin baik.\n"
            "- **Feature importance**: fitur yang paling banyak digunakan model saat membuat prediksi. "
            "Ini bukan bukti bahwa fitur itu menyebabkan polusi.\n"
            "- **Data training/validasi/testing**: model dilatih dengan data 2022-2024, disetel dengan data 2025, "
            "dan diuji dengan data 2026 yang belum pernah dilihatnya."
        )

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("metrik"):
            st.subheader("Perbandingan model")
            st.caption("Sel yang disorot hijau adalah nilai terbaik di kolomnya.")
            st.dataframe(
                metrik.style.format({"MAE": "{:.2f}", "RMSE": "{:.2f}", "R2": "{:.2f}"})
                .highlight_min(subset=["MAE", "RMSE"], color="#D7F0E8")
                .highlight_max(subset=["R2"], color="#D7F0E8"),
                hide_index=True, height=38 * (len(metrik) + 1) + 3,
            )
    with kanan:
        with kotak("mae"):
            st.subheader("MAE per model")
            st.caption("Batang lebih pendek berarti prediksi lebih jarang meleset.")
            m = metrik.sort_values("MAE", ascending=False)
            fig = px.bar(m, x="MAE", y="model", orientation="h", color_discrete_sequence=[WARNA_UTAMA])
            fig.update_yaxes(title=None)
            st.plotly_chart(pakai_tema(fig, 250))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("fitur"):
            st.subheader("Fitur yang paling banyak digunakan model")
            st.caption("Batang lebih panjang berarti fitur itu lebih sering dipakai model. "
                       "Fitur berawalan pm2_5 adalah riwayat PM2.5 hari-hari sebelumnya.")
            f = fitur.sort_values("importance")
            fig2 = px.bar(f, x="importance", y="feature", orientation="h", color_discrete_sequence=[WARNA_UTAMA])
            fig2.update_yaxes(title=None)
            fig2.update_xaxes(title="Feature importance")
            st.plotly_chart(pakai_tema(fig2, 360))
    with kanan:
        with kotak("aktual"):
            st.subheader("Aktual vs prediksi")
            st.caption("Setiap titik adalah satu hari di satu kabupaten/kota, diwarnai per provinsi. "
                       "Makin dekat titik ke garis putus-putus, makin tepat prediksinya.")
            e = contoh_model(tuple(pilih_kota))
            fig3 = px.scatter(e, x="pm2_5_aktual", y="pm2_5_prediksi", color="provinsi", opacity=0.5,
                              color_discrete_map=WARNA_PROVINSI,
                              labels={"pm2_5_aktual": "Aktual (µg/m³)", "pm2_5_prediksi": "Prediksi (µg/m³)",
                                      "provinsi": "Provinsi"})
            mx = float(max(e["pm2_5_aktual"].max(), e["pm2_5_prediksi"].max()))
            fig3.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines", name="Prediksi = aktual",
                                      line=dict(color="#8A9A95", dash="dot")))
            st.plotly_chart(pakai_tema(fig3, 360))


@st.fragment
def butuh_kota(fungsi):
    # fragment: widget di dalam tab hanya me-render ulang tab itu, bukan seluruh halaman
    if not pilih_kota:
        st.info("Pilih minimal satu provinsi di sidebar.")
    else:
        fungsi()


# ====================== PENGARAH HALAMAN ======================
if st.session_state.get("halaman", "landing") == "landing":
    landing()
    st.stop()

# --- Dashboard: sidebar ---
tmin, tmax = tgl_aktual.min().date(), tgl_aktual.max().date()
st.sidebar.markdown(
    f'<div class="brand"><div class="lg">{IKON["daun"]}</div>'
    '<div><div class="bn">AirGuard SDGs</div><div class="bs">Pulau Jawa</div></div></div>',
    unsafe_allow_html=True,
)
st.sidebar.header("Filter")
st.sidebar.caption("Berlaku untuk semua tab.")
pilih_prov = st.sidebar.multiselect("Provinsi", PROVINSI, default=PROVINSI)
kandidat = [k for k in semua_kota if PROV_DARI_KOTA[k] in pilih_prov]
dipilih = st.sidebar.multiselect("Kabupaten/kota", kandidat, placeholder="Semua yang sesuai filter di atas")
pilih_kota = [k for k in dipilih if k in kandidat] or kandidat
st.sidebar.caption(f"{len(pilih_kota)} dari {len(semua_kota)} kabupaten/kota ditampilkan.")
rentang = st.sidebar.date_input("Rentang tanggal", value=(tmin, tmax), min_value=tmin, max_value=tmax)
if isinstance(rentang, (tuple, list)) and len(rentang) == 2:
    t0, t1 = pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1])
else:
    t0, t1 = pd.Timestamp(tmin), pd.Timestamp(tmax)

st.sidebar.caption("Kategori risiko mengikuti ISPU untuk PM2.5. Ini aturan visualisasi proyek, bukan klaim medis.")

# Filter dihitung sekali per interaksi, lalu dipakai bersama oleh semua tab.
pred_f = pred[pred["kota"].isin(pilih_kota)]

# --- Dashboard: banner atas dan tab ---
with st.container(key="topbar"):
    kol_btn, kol_judul, kol_info = st.columns([1.2, 3.2, 3], vertical_alignment="center")
    kol_btn.button("← Beranda", key="kembali", on_click=kembali)
    kol_judul.markdown(
        '<div class="judul-dash">Dashboard kualitas udara</div>'
        f'<div class="sub-dash">Prediksi PM2.5 untuk {len(semua_kota)} kabupaten/kota di {len(PROVINSI)} provinsi Pulau Jawa</div>',
        unsafe_allow_html=True,
    )
    kol_info.markdown(
        f'<div style="text-align:right"><span class="glass">Data sampai {tmax:%d %b %Y}</span>'
        f'<span class="glass">Prediksi untuk {(tgl_aktual.max() + pd.Timedelta(days=1)):%d %b %Y}</span></div>',
        unsafe_allow_html=True,
    )

# on_change="rerun": hanya tab yang sedang dibuka yang dihitung, jadi masuk dan pindah tab lebih cepat.
# Hanya tab yang sedang aktif yang dihitung (tab lain dilewati), supaya dashboard terasa ringan.
tab_ringkasan, tab_tren, tab_cuaca, tab_model = st.tabs(
    ["Ringkasan", "Tren & Prediksi", "Cuaca", "Model"], key="tab_dash", on_change="rerun")
for tab, fungsi in [(tab_ringkasan, ringkasan), (tab_tren, tren), (tab_cuaca, cuaca), (tab_model, model)]:
    with tab:
        if tab.open:
            butuh_kota(fungsi)