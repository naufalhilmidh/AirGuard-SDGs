import urllib.parse

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (BATAS_TINGGI, kode_status, muat_cluster_rinci, muat_proyeksi, profil_unik, FAKTOR, KATEGORI, KODE_DARI_KOTA, KODE_DARI_PROV, KOTA, LABEL_ZONA,
                   PALET_KOTA, PROV_DARI_KOTA, PROVINSI, RAMP_WARNA, URUTAN_ZONA, WARNA_KATEGORI,
                   WARNA_PREDIKSI, WARNA_PROVINSI, WARNA_UTAMA, WARNA_ZONA, WILAYAH, jalur_peta,
                   muat_batas, muat_cluster, muat_data, nama_kategori, urai_path, warna_nilai)

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
    [data-testid="stTabs"] [role="tablist"] {gap: 8px !important; overflow: visible !important;
        margin-bottom: 1.2rem !important; justify-content: flex-start !important;}
    [data-testid="stTabs"] [role="tablist"]::after {display: none !important;}
    [data-testid="stTab"], button[data-baseweb="tab"] {
        flex: 0 0 auto !important; justify-content: flex-start !important; height: auto !important; margin: 0 !important;
        padding: .55rem 1.25rem !important; background: transparent !important; border: 1px solid #DDE5D6 !important;
        border-radius: 999px !important; color: #17302A !important;
    }
    [data-testid="stTab"] p, button[data-baseweb="tab"] p {font-size: 1rem !important; font-weight: 500 !important; color: #17302A !important;}
    [data-testid="stTab"]:hover, button[data-baseweb="tab"]:hover {background: #E3ECDD !important;}
    [data-testid="stTab"][data-selected], [data-testid="stTab"][aria-selected="true"],
    button[data-baseweb="tab"][aria-selected="true"] {background: #1F4D3E !important; border-color: #1F4D3E !important;}
    [data-testid="stTab"][data-selected] p, [data-testid="stTab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] p {color: #FFFFFF !important; font-weight: 600 !important;}
    [data-testid="stTab"] .react-aria-SelectionIndicator, div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {display: none !important;}

    /* daftar peringkat berupa batang horizontal, sebagai pengganti tabel penuh */
    .rlist {display: flex; flex-direction: column; gap: 7px;}
    /* varian dua jalur: selebar mungkin, tapi tetap boleh menyusut; tingginya tinggal separuh
       sehingga kartu "5 tertinggi" tidak lagi memaksa baris jadi tinggi */
    .rlist.k2 {display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
        column-gap: 24px; align-items: start; width: 100%;}
    .rlist.k2 .catatan {grid-column: 1 / -1;}
    .rlist.k2 .rname {white-space: normal; line-height: 1.25;}
    @media (max-width: 1200px) {.rlist.k2 {grid-template-columns: minmax(0, 1fr);}}
    .rrow {display: grid; grid-template-columns: 20px minmax(0, 1.4fr) minmax(60px, 1fr) 52px;
        align-items: center; gap: 8px;}
    .rrank {font-size: .78rem; font-weight: 600; color: #7A8B80; text-align: right; font-variant-numeric: tabular-nums;}
    .rname {font-size: .88rem; font-weight: 500; color: #17302A; white-space: nowrap; overflow: hidden;
        text-overflow: ellipsis;}
    .rbar {height: 8px; background: #E3E9D9; border-radius: 99px; overflow: hidden;}
    .rbar > span {display: block; height: 100%; border-radius: 99px;}
    .rval {font-size: .85rem; font-weight: 600; color: #17302A; text-align: right; font-variant-numeric: tabular-nums;}
    .rlist .catatan {font-size: .78rem; color: #5E6F65; margin-top: 2px;}
    .stApp h3 {font-size: 1.1rem !important; font-weight: 600 !important; padding: .4rem 0 .1rem !important; color: #17302A;}
    [class*="st-key-card_"] h3 {padding-top: 0 !important;}

    /* kartu */
    [class*="st-key-card_"], .kartu {
        background: #FBFCF8; border: 1px solid #DDE5D6; border-radius: 16px; padding: 18px 20px;
        box-shadow: 0 1px 2px rgba(23,48,42,.05), 0 8px 24px rgba(23,48,42,.05);
    }
    /* semua kartu dalam satu baris sama tinggi: Streamlit sudah menaruh stHorizontalBlock
       sebagai flex row, jadi cukup regangkan kartunya (defaultnya align-items: stretch) */
    [class*="st-key-card_"] {display: flex; flex-direction: column; height: 100%;}
    [class*="st-key-card_"] > [data-testid="stVerticalBlock"],
    [class*="st-key-card_"] > [data-testid="stElementContainer"] {flex: 1 1 auto; min-height: 0; width: 100%;}
    /* tabel & grafik di dalam kartu mengisi sisa ruang, bukan menyisakan celah di bawah */
    [class*="st-key-card_"] [data-testid="stDataFrame"],
    [class*="st-key-card_"] [data-testid="stPlotlyChart"],
    [class*="st-key-card_"] .js-plotly-plot {width: 100% !important;}
    /* intro bukan kartu biasa: latar hijau dipasang di KARTU-nya, bukan di blok di dalamnya.
       Kalau latarnya di elemen dalam, padding kartu (18/20 px) tetap terlihat sebagai pita krem
       di kiri-kanan-atas-bawah, jadi kotaknya tampak dobel dan tidak presisi. */
    [class*="st-key-card_intro"] {
        background: #E3ECDD; border: 1px solid #D8E3D2; border-radius: 14px;
        box-shadow: none; padding: 14px 18px; height: auto;
    }
    [class*="st-key-card_intro"] > [data-testid="stVerticalBlock"],
    [class*="st-key-card_intro"] > [data-testid="stElementContainer"] {gap: 0 !important;}
    .intro {background: none; border-radius: 0; padding: 0; font-size: .93rem; line-height: 1.6; color: #17302A;}
    /* paragraf dari st.markdown selalu menyisakan margin bawah; di dalam blok berwarna itu
       membuat teks terlihat meleset ke atas. Dirapatkan supaya jarak atas = jarak bawah. */
    [class*="st-key-card_intro"] [data-testid="stMarkdownContainer"] {margin: 0 !important;}
    [class*="st-key-card_intro"] [data-testid="stMarkdownContainer"] > :last-child {margin-bottom: 0 !important;}
    [class*="st-key-card_intro"] [data-testid="stMarkdownContainer"] > :first-child {margin-top: 0 !important;}
    .kartu.flat {border: none; box-shadow: none; padding: 0; background: none;}
    /* kartu HTML yang isinya sudah dirender di dalam kartu Streamlit: jangan digambar dua kali */
    .kartu.isi-kartu {background: none; border: none; box-shadow: none; border-radius: 0; padding: 0;}
    .grid {display: grid; gap: 16px; align-items: stretch; margin-bottom: 1rem; grid-auto-rows: 1fr;}
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
    @media (max-width: 900px) {.g3, .g4 {grid-template-columns: repeat(2, minmax(0, 1fr));}}

    /* banner berilustrasi (landing, bagian atas dashboard, ajakan penutup) */
    .st-key-hero, .st-key-topbar, .st-key-cta {
        background-color: #D6E8DC; background-size: cover; background-position: right bottom;
        background-repeat: no-repeat; border-radius: 20px; overflow: hidden;
        box-shadow: 0 1px 2px rgba(23,48,42,.06), 0 10px 28px rgba(23,48,42,.08);
    }
    .st-key-hero {padding: 40px 52px 44px;}
    .st-key-cta {padding: 26px 52px 30px;}
    .st-key-topbar {padding: 20px 28px;}
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

    /* Kursor di atas peta: plotly memakai panah empat arah (cursor-move) / crosshair yang
       terlihat kasar. Diganti penunjuk biasa supaya konsisten dengan wilayah yang bisa di-hover.
       Aturan plotly tidak pakai !important, jadi ini menang tanpa mengubah skrip plotly. */
    [class*="st-key-card_peta"] .js-plotly-plot,
    [class*="st-key-card_peta"] .js-plotly-plot .plot-container,
    [class*="st-key-card_peta"] .js-plotly-plot .draglayer,
    [class*="st-key-card_peta"] .js-plotly-plot .nsewdrag,
    [class*="st-key-card_peta"] .js-plotly-plot .cursor-move,
    [class*="st-key-card_peta"] .js-plotly-plot .cursor-crosshair,
    [class*="st-key-card_peta"] .js-plotly-plot .cursor-default {cursor: pointer !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

TEKS_KATEGORI = {"Baik": "#14231F", "Sedang": "#14231F", "Tidak sehat": "#FFFFFF"}
SARAN = {
    "Baik": "Kualitas udara baik. Aktivitas di luar ruangan aman dilakukan.",
    "Sedang": "Kelompok sensitif (anak, lansia, penderita asma) sebaiknya mengurangi aktivitas berat di luar ruangan.",
    "Tidak sehat": "Kurangi aktivitas berat di luar ruangan, terutama untuk kelompok sensitif. Pertimbangkan memakai masker bila harus keluar.",
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
    # Latar hijau dipasang lewat CSS pada kartu ber-key ini (bukan pada div di dalamnya),
    # supaya tidak ada padding kartu yang menyisakan bingkai krem di sekeliling kotak hijau.
    with st.container(key="card_intro"):
        st.markdown(f'<div class="intro">{teks}</div>', unsafe_allow_html=True)


def kotak(nama, tinggi=None):
    """Kartu ber-key. Kalau `tinggi` (px) diisi, kartu dikunci setinggi itu dan menata isinya
    selebar mungkin (flex) supaya padding kiri-kanan tidak dobel.

    Kenapa perlu: kartu yang isinya grafik bertinggi tetap tidak bisa "memanfaatkan sisa ruang" —
    slot-nya cuma setinggi elemen, sehingga tinggi induk yang dikunci jadi ikut terabaikan.
    """
    if tinggi is None:
        return st.container(key=f"card_{nama}")
    return st.container(key=f"card_{nama}", height=tinggi, border=False, gap="small")


KONFIG_PETA = {"displaylogo": False, "scrollZoom": False,
               "modeBarButtonsToRemove": ["select2d", "lasso2d", "toImage"]}

# Tinggi grafik dan "chrome" kartu (padding 36 + judul 30 + caption dua baris 40 + celah 16 + grafik
# + border 2 + celah bawah 36). Dipakai untuk baris kartu yang isinya grafik, supaya tinggi kartu
# dihitung, bukan ditebak.
CHART = 360
CHROME = 200


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


pred, pre, metrik, fitur, sumber, tak_cocok = muat_data()
FAKTOR = {k: v for k, v in FAKTOR.items() if k in pre.columns}  # data contoh tidak memuat polutan lain
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
    p1, p2 = st.columns([1, 1.3])
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
                f'Ringkasan umum berdasarkan tiga status AirGuard, bukan saran medis.</div></div>',
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


def catatan_sumber():
    """Peringatan jujur tentang asal prediksi. Data asli dan data contoh tidak pernah dicampur."""
    if sumber == "baseline":
        return ("Prediksi besok saat ini adalah baseline persistence (besok dianggap sama dengan hari ini) dari data asli, "
                "bukan model tim. Angkanya akan diganti otomatis setelah airguard_predictions.csv tersedia.")
    if sumber == "contoh":
        return "Memakai data contoh (sintetis), bukan data asli. Taruh file tim di data/data_gabungan untuk data sebenarnya."
    return ""


# ====================== LANDING PAGE ======================
def landing():
    terakhir = tgl_aktual.max()
    besok = terakhir + pd.Timedelta(days=1)

    with st.container(key="hero"):
        st.markdown(
            '<div class="eyebrow">SDG 3 · SDG 11 · SDG 13</div>'
            '<h1>AirGuard SDGs</h1>'
            '<p class="lead">Prediksi dan pemetaan risiko PM2.5 hari berikutnya untuk kabupaten dan kota di Pulau Jawa. '
            'Data kualitas udara harian dari Open-Meteo dipakai untuk memprediksi konsentrasi PM2.5 esok hari, '
            'lalu ditampilkan dalam bentuk peta, tren, dan kategori risiko.</p>'
            f'<span class="glass">{len(semua_kota)} kabupaten/kota, {len(PROVINSI)} provinsi</span>'
            f'<span class="glass">Data aktual sampai {terakhir:%d %b %Y}</span>'
            f'<span class="glass">Prediksi untuk {besok:%d %b %Y}</span>'
            + {"baseline": '<span class="glass">Prediksi: baseline persistence</span>',
               "contoh": '<span class="glass">Data contoh (sintetis)</span>'}.get(sumber, ""),
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
              "Pola polusi dibaca bersama musim untuk memahami kapan polusi meningkat.", chip("SDG 13")),
    )

    st.subheader("Yang bisa kamu lihat di dashboard")
    grid(
        "g3",
        kartu("Ringkasan", "Status besok (Baik, Sedang, Tidak sehat), peta Pulau Jawa, dan peringkat per kabupaten/kota atau provinsi."),
        kartu("Tren & Prediksi", "PM2.5 aktual dibandingkan prediksi, plus daftar episode polusi tinggi."),
        kartu(f"Proyeksi {tgl_aktual.max().year + 1}", "Bulan dan provinsi yang cenderung tinggi sepanjang tahun depan, lengkap dengan kalender risiko."),
        kartu("Faktor Lain", "Pola PM2.5 yang bergerak bersama polutan lain (PM10, NO₂, SO₂, CO, ozon) dan riwayatnya sendiri."),
        kartu("Klaster wilayah", "Pengelompokan kabupaten/kota menjadi tiga zona menurut karakter polusi jangka panjang."),
        kartu("Model", "Seberapa akurat prediksi pada data uji, termasuk kemampuan memperingatkan hari Tidak sehat."),
    )

    with st.container(key="cta"):
        st.markdown('<div class="ctaT">Siap melihat datanya?</div>'
                    '<div class="ctaS">Buka dashboard untuk peta risiko, tren, proyeksi tahun depan, klaster wilayah, dan performa model.</div>',
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
    # Peta memakai gradasi di antara ambang ini, jadi legenda menampilkan ramp-nya juga.
    gradasi = ", ".join(warna for _, warna in RAMP_WARNA)
    return (f'<div class="kartu flat">'
            f'<div class="isi" style="margin-bottom:6px">PM2.5 harian (µg/m³), tiga status AirGuard.</div>'
            f'<div style="height:9px;border-radius:6px;margin-bottom:8px;'
            f'background:linear-gradient(90deg,{gradasi})"></div>'
            f'{"".join(baris)}</div>')


@st.cache_data(show_spinner=False)
def lapisan_peta(level):
    """Satu baris per ring (pulau/bagian wilayah): kode, nama, array x, array y.

    Dipakai untuk menggambar peta sebagai Scatter SVG. Tiap ring jadi trace sendiri supaya
    fill="toself" hanya menutup satu poligon — tidak bergantung pada cara plotly menangani
    titik pemisah antar pulau dalam satu trace.
    """
    data = jalur_peta(level)
    if data is None:
        return None
    hasil = []
    for kode, nama, d in data["fitur"]:
        for titik in urai_path(d):
            hasil.append((kode, nama, [p[0] for p in titik], [p[1] for p in titik]))
    return hasil


def peta_interaktif(level, warna, tips, tinggi=440):
    """Peta choropleth interaktif tanpa WebGL: satu go.Scatter (fill="toself") per wilayah.

    Trace peta bawaan plotly berbasis WebGL, dan di sebagian perangkat isi poligonnya tidak
    tergambar sama sekali (yang tampil hanya basemap abu-biru). Scatter memakai SVG biasa:
    warnanya juga literal per wilayah, jadi tidak mungkin berbeda dari legenda, sementara
    hover, drag, dan zoom tetap berfungsi.
    """
    lapisan = lapisan_peta(level)
    if not lapisan:
        return None
    fig = go.Figure()
    for kode, nama, xs, ys in lapisan:
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", fill="toself", fillcolor=warna.get(kode, "#D8D8D8"),
            line=dict(color="#FFFFFF", width=0.4), hoveron="fills",
            text=tips.get(kode, nama), hovertemplate="%{text}<extra></extra>",
            name=nama, showlegend=False,
            hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#DCE6E2", align="left",
                            font=dict(family="IBM Plex Sans, sans-serif", size=12, color="#17302A")),
        ))
    fig.update_layout(
        template="simple_white", height=tinggi, showlegend=False, dragmode="pan",
        margin=dict(l=2, r=2, t=2, b=2), hovermode="closest",
        # zoom/geser tetap tersimpan saat tanggal di sidebar diganti; tapi direset saat
        # pindah kab/kota <-> provinsi karena cakupan petanya berbeda
        uirevision=f"peta-{level}",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        # skala y dikunci ke x supaya bentuk pulau tidak gepeng saat kotak peta di-zoom
        yaxis=dict(visible=False, autorange="reversed", scaleanchor="x", scaleratio=1),
    )
    return fig


def legenda_zona(klaster, u):
    """Legenda zona cluster: sengaja terpisah dari legenda kategori risiko."""
    if klaster is None:
        return ('<div class="kartu flat"><div class="isi">Hasil clustering belum tersedia.'
                '</div></div>')
    gab = u[["kode"]].merge(klaster, on="kode", how="left")
    baris = []
    for zona in URUTAN_ZONA:
        sub = gab[gab["zona"] == zona]
        rerata = f"{sub['rata_rata_pm25'].mean():.0f} µg/m³" if len(sub) else "–"
        baris.append(f'<div class="kat"><span class="dot" style="background:{WARNA_ZONA[zona]}"></span>'
                     f'<span>{LABEL_ZONA[zona]}</span>'
                     f'<span class="rg">{len(sub)} wilayah · {rerata}</span></div>')
    return ('<div class="kartu flat">'
            '<div class="isi" style="margin-bottom:6px">K-Means (k=3) atas karakter jangka panjang '
            'tiap wilayah: rata-rata, median, maksimum, variabilitas, episode, dan polutan lain. '
            'Warna hanya pembeda zona, bukan tingkat bahaya harian.</div>'
            f'{"".join(baris)}</div>')


def daftar_bar(u, kolom, n=10, kolom_kategori=None, catatan="", kisi=None):
    """Peringkat ringkas berupa batang horizontal (HTML), diurutkan dari nilai terbesar.

    `kisi=2` membaginya jadi dua jalur (kiri 1..n/2, kanan sisanya): untuk n=10 tinggi daftar
    tinggal separuh, jadi kartunya tidak memaksa baris jadi tinggi.
    """
    d = u.nlargest(int(n), kolom)
    puncak = max(float(d[kolom].max()), 1e-9) if len(d) else 1.0
    pakai_kategori = bool(kolom_kategori) and kolom_kategori in u.columns
    baris = []
    for i, (_, r) in enumerate(d.iterrows(), 1):
        nilai = float(r[kolom])
        lebar = max(nilai / puncak * 100, 2)
        warna = WARNA_KATEGORI.get(str(r[kolom_kategori]), WARNA_UTAMA) if pakai_kategori else WARNA_UTAMA
        baris.append(
            f'<div class="rrow"><span class="rrank">{i}</span>'
            f'<span class="rname">{r["Wilayah"]}</span>'
            f'<span class="rbar"><span style="width:{lebar:.0f}%;background:{warna}"></span></span>'
            f'<span class="rval">{nilai:.1f}</span></div>')
    ekor = f'<div class="catatan">{catatan}</div>' if catatan else ""
    if kisi and kisi > 1 and len(baris) >= kisi * 2:
        per = -(-len(baris) // kisi)  # jumlah baris tiap jalur, dibulatkan ke atas
        jalur = "".join(f'<div class="rcol">{"".join(baris[i:i + per])}</div>'
                        for i in range(0, len(baris), per))
        return f'<div class="rlist k{kisi}">{jalur}{ekor}</div>'
    return f'<div class="rlist">{"".join(baris)}{ekor}</div>'


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

    # Pemilihan daerah di halaman ini: provinsi, lalu kabupaten/kota untuk kartu detail.
    f1, f2, f3 = st.columns([1, 1.4, 1.2], vertical_alignment="bottom")
    prov_pilih = f1.selectbox("Provinsi", ["Semua provinsi", *[p_ for p_ in PROVINSI if p_ in set(tabel["Provinsi"])]],
                              key="prov_ringkasan")
    if prov_pilih != "Semua provinsi":
        tabel = tabel[tabel["Provinsi"] == prov_pilih].reset_index(drop=True)
    opsi_k = sorted(tabel["kota"])
    kota_detail = f2.selectbox("Kabupaten/kota untuk kartu detail", opsi_k,
                               index=opsi_k.index(max(opsi_k, key=lambda k: (TIPE_DARI_KOTA[k] == "Kota", PENDUDUK[k]))),
                               key=f"kota_detail_{prov_pilih}", help="Ketik untuk mencari nama.")
    tgl_besok = terakhir + pd.Timedelta(days=1)
    unduh = tabel[["kota", "Provinsi", "PM2.5 hari ini", "Prediksi besok"]].rename(columns={
        "kota": "kabupaten_kota", "Provinsi": "provinsi", "PM2.5 hari ini": "pm2_5_hari_ini",
        "Prediksi besok": "pm2_5_prediksi_besok"})
    unduh["status"] = unduh["pm2_5_prediksi_besok"].map(nama_kategori)
    f3.download_button("Unduh status besok (CSV)", unduh.round(2).to_csv(index=False).encode("utf-8"),
                       file_name=f"airguard_status_{tgl_besok:%Y%m%d}.csv", mime="text/csv", use_container_width=True)

    if prov_pilih == "Semua provinsi":
        tingkat = st.radio("Tampilkan per", ["Kabupaten/kota", "Provinsi"], horizontal=True, key="tingkat_ringkasan")
    else:
        tingkat = "Kabupaten/kota"
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
    t["kode"] = t["Wilayah"].map(KODE_DARI_PROV if per_prov else KODE_DARI_KOTA)

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

    # Jumlah kabupaten/kota per status besok, dibanding status hari ini.
    sb = pd.Series(kode_status(tabel["Prediksi besok"].to_numpy())).value_counts().reindex(range(3), fill_value=0)
    si = pd.Series(kode_status(tabel["PM2.5 hari ini"].to_numpy())).value_counts().reindex(range(3), fill_value=0)
    pastel_st = ["#DCEBD8", "#F8E7C4", "#F4D5D1"]
    ikon_st = ["daun", "angin", "awas"]
    kartu_st = []
    for i, (_, nama_st, _) in enumerate(KATEGORI):
        d_st = int(sb[i] - si[i])
        ket_st = "sama seperti hari ini" if d_st == 0 else f"{d_st:+d} dibanding hari ini ({int(si[i])})"
        kartu_st.append(stat(f"Status {nama_st} besok", f"{int(sb[i])} kab/kota", ket_st, ikon_st[i], pastel_st[i]))
    grid("g3", *kartu_st)

    # Kota-kota besar: pembacaan cepat untuk masyarakat umum.
    ada_tipe = tabel.assign(tipe=tabel["kota"].map(TIPE_DARI_KOTA), pend=tabel["kota"].map(PENDUDUK))
    besar = ada_tipe[ada_tipe["tipe"] == "Kota"]
    besar = (besar if not besar.empty else ada_tipe).sort_values("pend", ascending=False).head(6)
    st.subheader("Status kota-kota besar besok")
    def kartu_besar(r):
        v = r["Prediksi besok"]
        kat = nama_kategori(v)
        return (f'<div class="kartu"><div class="isi" style="margin:0">{r["kota"]}</div>'
                f'<div class="besar" style="font-size:1.6rem">{v:.0f} '
                f'<span style="font-size:.85rem;font-weight:500;color:#5A6B66">µg/m³</span></div>'
                f'<span class="pill" style="background:{WARNA_KATEGORI[kat]};color:{TEKS_KATEGORI[kat]}">{kat}</span></div>')
    grid("g3", *[kartu_besar(r) for _, r in besar.iterrows()])

    kiri, kanan = st.columns([2.15, 1], gap="large")
    with kiri:
        with kotak("peta"):
            # Dua peta yang berbeda tujuan (requirement.md 6.5/6.6): peta risiko menjawab
            # "berapa nilai PM2.5 besok", peta zona menjawab "wilayah ini karakternya apa".
            # Zona cluster hanya ada per kabupaten/kota, bukan per provinsi.
            if per_prov:
                mode_peta = "Risiko besok"
            else:
                mode_peta = st.segmented_control(
                    "Tampilan peta", ["Risiko besok", "Zona cluster"],
                    default="Risiko besok", key="mode_peta", label_visibility="collapsed",
                ) or "Risiko besok"
            if mode_peta == "Zona cluster":
                st.subheader("Peta zona cluster")
                st.caption("Zona hasil K-Means (k=3) atas karakter jangka panjang tiap wilayah, jadi "
                           "sifatnya tetap: tidak berubah saat tanggal di sidebar diganti. Arahkan "
                           "kursor ke wilayah untuk melihat karakteristiknya, tarik untuk menggeser, "
                           "gulir-ganda untuk kembali.")
            else:
                st.subheader("Peta risiko besok")
                st.caption("Warna wilayah mengikuti besar nilai PM2.5 yang diprediksi untuk besok "
                           "(makin ke merah, makin tinggi). Arahkan kursor ke wilayah untuk melihat "
                           "angkanya."
                           + (" Peta zona cluster hanya tersedia pada tampilan kabupaten/kota."
                              if per_prov else ""))
            level_peta = "provinsi" if per_prov else "kabkota"
            batas = muat_batas(level_peta)
            kolom_info = "Berisiko tinggi besok" if per_prov else "Provinsi"
            ekor = " wilayah berisiko tinggi" if per_prov else ""
            if batas is None:
                st.info("Berkas batas wilayah belum ada. Jalankan sekali dari folder dashboard: "
                        "`python referensi/buat_batas.py`")
            elif t["kode"].isna().any():
                st.warning("Ada wilayah tanpa kode BPS sehingga tidak bisa digambar pada peta.")
            elif mode_peta == "Zona cluster":
                klaster = muat_cluster()
                if klaster is None:
                    st.info("Hasil clustering belum ada di `data/data_gabungan/clustering_wilayah.csv`. "
                            "Jalankan notebooks/04_modeling/CLUSTERING.ipynb lebih dulu.")
                else:
                    gab = t[["kode", "Wilayah"]].merge(klaster, on="kode", how="left")
                    hilang = gab.loc[gab["zona"].isna(), "Wilayah"].tolist()
                    if hilang:
                        st.warning("Belum punya zona cluster: " + ", ".join(hilang[:5])
                                   + (f" (+{len(hilang) - 5} lagi)" if len(hilang) > 5 else ""))
                    warna, tips = {}, {}
                    for kode, wilayah, zona, rata, persen in zip(
                            gab["kode"], gab["Wilayah"], gab["zona"],
                            gab["rata_rata_pm25"], gab["persentase_hari_tinggi"]):
                        kenal = isinstance(zona, str) and zona in WARNA_ZONA
                        warna[kode] = WARNA_ZONA[zona] if kenal else "#D8D8D8"
                        rata_txt = f"{rata:.1f}" if rata == rata else "–"
                        persen_txt = f"{persen:.1f}" if persen == persen else "–"
                        tips[kode] = (f"<b>{wilayah}</b><br>Zona "
                                      f"{LABEL_ZONA[zona] if kenal else 'belum ada data'}"
                                      f"<br>Rata-rata PM2.5 jangka panjang {rata_txt} µg/m³"
                                      f"<br>Hari bernilai tinggi {persen_txt}%")
                    peta = peta_interaktif("kabkota", warna, tips)
                    if peta:
                        st.plotly_chart(peta, config=KONFIG_PETA, key="peta_zona")
            else:
                # Warna = besar nilai prediksi (gradasi), bukan warna kategori, supaya selisih
                # kecil antar wilayah tetap terbaca: 92% wilayah memang sekategori "Sedang".
                # Titik henti warnanya mengikuti ambang status, jadi tetap bermakna.
                warna, tips = {}, {}
                for kode, wilayah, besok, hari_ini, kategori, info in zip(
                        t["kode"], t["Wilayah"], t["Prediksi besok"], t["PM2.5 hari ini"],
                        t["Kategori besok"], t[kolom_info]):
                    warna[kode] = warna_nilai(besok)
                    besok_txt = f"{besok:.1f}" if besok == besok else "–"
                    hari_txt = f"{hari_ini:.1f}" if hari_ini == hari_ini else "–"
                    tips[kode] = (f"<b>{wilayah}</b><br>Prediksi besok {besok_txt} µg/m³ "
                                  f"(hari ini {hari_txt})<br>Kategori {kategori}"
                                  f"<br>{info}{ekor}")
                peta = peta_interaktif(level_peta, warna, tips)
                if peta:
                    st.plotly_chart(peta, config=KONFIG_PETA, key="peta_risiko")
    with kanan:
        with kotak("detail"):
            r = tabel[tabel["kota"] == kota_detail].iloc[0]
            kat_d = nama_kategori(r["Prediksi besok"])
            beda = r["Prediksi besok"] - r["PM2.5 hari ini"]
            ubah = "tetap" if abs(beda) < 0.05 else ("naik " if beda > 0 else "turun ") + f"{abs(beda):.1f}"
            angin_txt = ""
            if "wind_speed_10m" in pre.columns:
                kmh = pre[(pre["kota"] == kota_detail) & (pre["tanggal"] == terakhir)]["wind_speed_10m"]
                if len(kmh) and kmh.iloc[0] == kmh.iloc[0]:
                    kmh = float(kmh.iloc[0])
                    vent = "lemah" if kmh < 7.2 else ("sedang" if kmh < 14.4 else "baik")
                    angin_txt = (f'<div class="isi">Angin hari ini: <b>{kmh:.1f} km/jam</b> · ventilasi udara <b>{vent}</b> '
                                 '(batas indikatif)</div>')
            st.markdown(
                f'<div class="jud">{kota_detail}</div>'
                f'<div class="isi">{r["Provinsi"]} · prediksi untuk {tgl_besok:%d %b %Y}</div>'
                f'<div class="besar">{r["Prediksi besok"]:.1f} <span style="font-size:1rem;font-weight:500;color:#5A6B66">µg/m³</span></div>'
                f'<span class="pill" style="background:{WARNA_KATEGORI[kat_d]};color:{TEKS_KATEGORI[kat_d]}">{kat_d}</span>'
                f'<div class="isi" style="margin-top:12px">PM2.5 hari ini (aktual) <b>{r["PM2.5 hari ini"]:.1f}</b> · {ubah}</div>'
                f'{angin_txt}'
                f'<div class="isi" style="margin-top:8px">{SARAN[kat_d]}</div>'
                f'<div class="isi" style="margin-top:10px;font-size:.8rem;color:#5A6B66">'
                f'Ringkasan umum berdasarkan tiga status AirGuard, bukan saran medis.</div>',
                unsafe_allow_html=True)
        with kotak("risiko"):
            st.subheader("5 tertinggi besok")
            st.markdown(daftar_bar(t, "Prediksi besok", 5, kolom_kategori="Kategori besok",
                                   catatan="Angka dalam µg/m³."),
                        unsafe_allow_html=True)
        with kotak("legenda"):
            # Legenda mengikuti mode peta: zona cluster dan kategori risiko tidak pernah digabung.
            if mode_peta == "Zona cluster":
                st.subheader("Keterangan zona")
                st.markdown(legenda_zona(muat_cluster(), t), unsafe_allow_html=True)
                st.caption("Butuh angka harian? Pindah ke mode \"Risiko besok\".")
            else:
                st.subheader("Keterangan warna")
                st.markdown(legenda_kategori(), unsafe_allow_html=True)
                st.caption("Butuh karakter wilayah? Pindah ke mode \"Zona cluster\".")

    with kotak("peringkat"):
        st.subheader("Peringkat " + ("provinsi" if per_prov else "kabupaten/kota"))
        f1, f2 = st.columns(2)
        urut = f1.selectbox("Urutkan berdasarkan", ["Prediksi besok", "PM2.5 hari ini", "Rata-rata periode"],
                            key="urut_peringkat")
        if per_prov:
            jumlah = len(t)
            # sebelah kanan kosong: keterangan ditaruh di sana, bukan menyisakan kolom menganga
            f2.caption("Provinsi selalu ditampilkan semua.")
        else:
            pilihan = f2.selectbox("Tampilkan", ["10 teratas", "20 teratas", "Semua"], key="jml_peringkat")
            jumlah = len(t) if pilihan == "Semua" else int(pilihan.split()[0])
        kolom = ["Wilayah", "Jumlah wilayah", "Berisiko tinggi besok"] if per_prov else ["Wilayah", "Provinsi"]
        kolom += ["PM2.5 hari ini", "Prediksi besok", "Perubahan", "Rata-rata periode", "Kategori besok"]
        urutan = t.sort_values(urut, ascending=False)
        tampil = urutan.head(jumlah)[kolom].rename(
            columns={"Wilayah": "Provinsi" if per_prov else "Kabupaten/kota", "Jumlah wilayah": "Jumlah kab/kota"})
        st.markdown(
            daftar_bar(urutan, urut, min(jumlah, 12), kisi=2,
                       catatan="Batang = " + urut.lower() + ". Peringkat penuh dan unduhan ada di tabel lengkap."),
            unsafe_allow_html=True)
        with st.expander("Tabel lengkap (" + str(len(tampil)) + " baris)"):
            st.dataframe(
                tampil, hide_index=True, height=min(35 * len(tampil) + 38, 460),
                column_config={
                    "PM2.5 hari ini": st.column_config.NumberColumn(format="%.1f"),
                    "Prediksi besok": st.column_config.NumberColumn(format="%.1f"),
                    "Perubahan": st.column_config.NumberColumn(format="%+.1f"),
                    "Rata-rata periode": st.column_config.NumberColumn(format="%.1f"),
                },
            )
            st.caption("Satuan PM2.5: µg/m³. Perubahan = prediksi besok dikurangi PM2.5 hari ini. "
                       "Rata-rata periode dihitung dari rentang tanggal di sidebar.")


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

    f0, f1, f2 = st.columns([1.5, 1.4, 1.1], gap="large")
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
                             help="Bawaan: batas atas status Sedang (55 µg/m³).")

    d = d.sort_values("tanggal_prediksi").copy()
    d["error"] = d["pm2_5_prediksi"] - d["pm2_5_aktual"]
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
                                 line=dict(color=WARNA_KATEGORI["Tidak sehat"], width=1,
                                           dash="longdash")))
        fig.update_yaxes(title="PM2.5 (µg/m³)")
        st.plotly_chart(pakai_tema(fig, 380))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("error", tinggi=CHART + 90):
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
        with kotak("episode", tinggi=CHART + 90):
            st.subheader("Episode polusi tinggi")
            st.caption("Periode hari-hari berturut-turut ketika PM2.5 aktual melewati ambang. "
                       "Puncak adalah nilai tertinggi dalam periode itu.")
            ep = episode(d, ambang)
            if ep.empty:
                st.write("Tidak ada hari di atas ambang pada rentang ini.")
            else:
                st.dataframe(ep, hide_index=True, height=min(35 * len(ep) + 38, 300),
                             column_config={"Puncak": st.column_config.NumberColumn(format="%.1f")})


@st.cache_data(show_spinner=False, max_entries=48)
def hitung_cuaca(daftar_kota, awal, akhir, grup):
    """Agregasi berat untuk tab Faktor Lain. Di-cache per kombinasi filter supaya tidak dihitung ulang.

    `grup` di sini adalah NAMA KOLOM ("provinsi" / "kota"), bukan label tampilan. Dulu yang
    di-groupby adalah variabel string literalnya, sehingga semua kota di Jawa ikut dirata-ratakan
    menjadi satu deret per tanggal: korelasi keluar sebagai satu baris saja, dan setiap baris
    heatmap menampilkan angka yang sama untuk provinsi berbeda.
    """
    d = pre[pre["kota"].isin(daftar_kota) & pre["tanggal"].between(awal, akhir)]
    harian = d.groupby([grup, "tanggal"], as_index=False, observed=True)[["pm2_5", *FAKTOR]].mean()
    korelasi = pd.DataFrame({
        k: g[list(FAKTOR)].corrwith(g["pm2_5"]) for k, g in harian.groupby(grup, observed=True)
    }).T.rename(columns=FAKTOR)
    bulanan = d.assign(bulan=d["tanggal"].dt.month).groupby(["bulan", grup], as_index=False, observed=True)["pm2_5"].mean()
    contoh = d.sample(min(len(d), 1500), random_state=0)[["kota", "provinsi", "pm2_5", *FAKTOR]].copy()
    contoh["kota"] = contoh["kota"].astype(str)
    contoh["provinsi"] = contoh["provinsi"].astype(str)
    bulanan[grup] = bulanan[grup].astype(str)
    korelasi.index = korelasi.index.astype(str)
    return korelasi, bulanan, contoh


def cuaca():
    if not FAKTOR:
        st.info("Data yang dimuat tidak berisi polutan lain untuk dikorelasikan dengan PM2.5.")
        return
    intro("<b>Halaman ini menjawab:</b> apakah PM2.5 cenderung naik atau turun bersamaan dengan polutan lain "
          "seperti PM10, NO₂, SO₂, dan ozon, atau mengikuti riwayatnya sendiri? Hubungan yang terlihat adalah "
          "<i>pola yang berkaitan</i>, bukan bukti sebab-akibat.")

    if len(pilih_kota) <= 12:
        grup_nama = st.radio("Kelompokkan per", ["Provinsi", "Kabupaten/kota"], horizontal=True, key="grup_cuaca")
    else:
        grup_nama = "Provinsi"
        st.caption("Dikelompokkan per provinsi. Pilih 12 kabupaten/kota atau kurang di sidebar kalau ingin melihat per daerah.")
    grup = "provinsi" if grup_nama == "Provinsi" else "kota"
    korelasi, bulanan, contoh = hitung_cuaca(tuple(pilih_kota), t0, t1, grup)
    warna = WARNA_PROVINSI if grup == "provinsi" else dict(zip(sorted(contoh["kota"].unique()), PALET_KOTA * 2))

    with kotak("korelasi"):
        st.subheader("Korelasi PM2.5 dengan faktor lain")
        st.caption("Angka (r) berkisar dari -1 sampai +1. Mendekati +1 (merah): PM2.5 cenderung naik saat variabel itu naik. "
                   "Mendekati -1 (biru): PM2.5 cenderung turun saat variabel itu naik. "
                   "Mendekati 0: hampir tidak ada pola."
                   + (" Tiap baris memakai rata-rata harian semua kabupaten/kota di provinsi itu." if grup == "provinsi" else ""))
        fig = px.imshow(korelasi, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
        fig.update_layout(coloraxis_colorbar=dict(title="r", thickness=12))
        fig.update_xaxes(side="top")
        st.plotly_chart(pakai_tema(fig, 130 + 52 * len(korelasi)))

    var = st.selectbox("Faktor pembanding", list(FAKTOR), format_func=FAKTOR.get)
    # tinggi kartu dikunci dalam piksel (bukan stretch): isi kartu ini adalah grafik dengan
    # tinggi tetap, jadi "sisa ruang" tidak ada gunanya dan malah bikin tinggi induk diabaikan
    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("sebar", tinggi=CHART + CHROME):
            st.subheader("PM2.5 dan satu faktor lain")
            st.caption("Setiap titik adalah satu hari di satu kabupaten/kota. Kalau sebaran titik naik ke kanan, "
                       "PM2.5 cenderung naik bersama faktor yang dipilih.")
            fig2 = px.scatter(contoh, x=var, y="pm2_5", color=grup, opacity=0.55, color_discrete_map=warna,
                              labels={var: FAKTOR[var], "pm2_5": "PM2.5 (µg/m³)", grup: grup_nama})
            st.plotly_chart(pakai_tema(fig2, CHART))
    with kanan:
        with kotak("bulanan", tinggi=CHART + CHROME):
            st.subheader("Rata-rata PM2.5 per bulan")
            st.caption("Bulan dengan nilai tinggi menunjukkan musim polusi pada data ini. "
                       "Berguna untuk melihat pola musiman tiap " + grup_nama.lower() + ".")
            fig3 = px.line(bulanan, x="bulan", y="pm2_5", color=grup, markers=True, color_discrete_map=warna,
                           labels={"bulan": "Bulan", "pm2_5": "PM2.5 (µg/m³)", grup: grup_nama})
            fig3.update_xaxes(tickmode="array", tickvals=list(range(1, 13)),
                              ticktext=["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"])
            st.plotly_chart(pakai_tema(fig3, CHART))


# ====================== EVALUASI MODEL (data uji) ======================
UJI_MULAI = pd.Timestamp("2026-01-01")
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember"]
BULAN_PENDEK = [b[:3] for b in BULAN]
NAMA_STATUS = [k[1] for k in KATEGORI]
LABEL_FITUR = {
    "pm2_5_lag_1": "PM2.5 kemarin", "pm2_5_lag_7": "PM2.5 tujuh hari lalu", "pm2_5": "PM2.5 hari ini",
    "pm2_5_rolling_3": "Rata-rata PM2.5 3 hari", "pm2_5_rolling_7": "Rata-rata PM2.5 7 hari",
    "bulan": "Bulan (pola musiman)", "wind_speed_10m": "Kecepatan angin",
    "relative_humidity_2m": "Kelembapan", "precipitation": "Curah hujan", "temperature_2m": "Suhu",
    "surface_pressure": "Tekanan udara", "cloud_cover": "Tutupan awan",
}


def data_uji():
    """Pasangan prediksi-aktual untuk evaluasi: data uji sejak 1 Jan 2026 (pembagian waktu tim).
    Kalau terlalu sedikit (misalnya data contoh), seluruh pasangan dipakai."""
    ada = pred[pred["pm2_5_aktual"].notna()]
    uji = ada[ada["tanggal_prediksi"] >= UJI_MULAI]
    if len(uji) < 1000:
        return ada, "seluruh periode"
    return uji, f"{uji['tanggal_prediksi'].min():%d %b %Y} sampai {uji['tanggal_prediksi'].max():%d %b %Y}"


@st.cache_data(show_spinner=False, max_entries=24)
def evaluasi(daftar_kota):
    """Metrik regresi, pembanding persistence, galat per bulan dan matriks konfusi 3 status."""
    uji, _ = data_uji()
    d = uji[uji["kota"].isin(daftar_kota)].sort_values(["kota", "tanggal_prediksi"])
    a, p = d["pm2_5_aktual"].to_numpy(float), d["pm2_5_prediksi"].to_numpy(float)
    e = p - a
    mae, rmse, bias = float(np.abs(e).mean()), float(np.sqrt((e ** 2).mean())), float(e.mean())
    r2 = float(1 - (e ** 2).sum() / ((a - a.mean()) ** 2).sum())

    # pembanding persistence ("besok = hari ini"): hanya pasangan hari berurutan dalam satu kota
    kode = pd.factorize(d["kota"])[0]
    tgl = d["tanggal_prediksi"].to_numpy()
    sah = np.r_[False, (kode[1:] == kode[:-1]) & ((tgl[1:] - tgl[:-1]) == np.timedelta64(1, "D"))]
    pers = np.r_[np.nan, a[:-1]]
    if sah.any():
        mae_pers = float(np.abs(a - pers)[sah].mean())
        skill = 1 - float(np.abs(e)[sah].mean()) / mae_pers if mae_pers > 0 else np.nan
    else:
        mae_pers, skill = np.nan, np.nan

    bulan = pd.Series(np.abs(e), index=d.index).groupby(d["tanggal_prediksi"].dt.month).mean()
    prov = (pd.DataFrame({"provinsi": d["provinsi"].astype(str).to_numpy(), "ae": np.abs(e)})
            .groupby("provinsi")["ae"].mean().reindex([p_ for p_ in PROVINSI]).dropna().rename("MAE").reset_index())
    cm = np.zeros((3, 3), dtype=int)
    np.add.at(cm, (d["st_aktual"].to_numpy(int), d["st_prediksi"].to_numpy(int)), 1)
    rng = np.random.default_rng(0)
    sampel_e = e[rng.choice(len(e), min(len(e), 20000), replace=False)]
    s = d.sample(min(len(d), 1500), random_state=0)[["provinsi", "pm2_5_aktual", "pm2_5_prediksi"]].copy()
    s["provinsi"] = s["provinsi"].astype(str)
    return dict(n=len(d), mae=mae, rmse=rmse, r2=r2, bias=bias, mae_pers=mae_pers, skill=skill,
                bulan=bulan, prov=prov, cm=cm, sampel_e=sampel_e, sebar=s)


def temuan(ev):
    t = []
    if abs(ev["bias"]) < 0.05 * ev["mae"]:
        bias_teks = "Hampir tanpa bias: kelebihan dan kekurangan prediksi saling mengimbangi."
    else:
        bias_teks = f"Bias {ev['bias']:+.1f}: rata-rata prediksi cenderung {'terlalu tinggi' if ev['bias'] > 0 else 'terlalu rendah'}."
    t.append(f"Prediksi rata-rata meleset <b>{ev['mae']:.1f} µg/m³</b> (RMSE {ev['rmse']:.1f}, R² {ev['r2']:.2f}). {bias_teks}")
    if sumber == "baseline":
        t.append("Prediksi yang dievaluasi adalah <b>baseline persistence</b> (besok = hari ini), bukan model tim. "
                 "Angka ini batas bawah yang harus dikalahkan model.")
    elif not np.isnan(ev["skill"]):
        if ev["skill"] > 0:
            t.append(f"Dibanding tebakan sederhana <i>persistence</i> (MAE {ev['mae_pers']:.1f}), "
                     f"galat model <b>{ev['skill'] * 100:.0f}% lebih rendah</b>.")
        else:
            t.append(f"Model <b>belum mengalahkan</b> persistence (MAE {ev['mae_pers']:.1f}); "
                     f"galatnya {abs(ev['skill']) * 100:.0f}% lebih tinggi.")
    g = ev["prov"]
    if len(g) > 1:
        t.append(f"Galat terbesar ada di <b>{g.loc[g['MAE'].idxmax(), 'provinsi']}</b> (MAE {g['MAE'].max():.1f}), "
                 f"terkecil di <b>{g.loc[g['MAE'].idxmin(), 'provinsi']}</b> (MAE {g['MAE'].min():.1f}).")
    b = ev["bulan"]
    if len(b) > 3:
        t.append(f"Bulan paling sulit diprediksi: <b>{BULAN[int(b.idxmax()) - 1]}</b> (MAE {b.max():.1f}); "
                 f"paling mudah: {BULAN[int(b.idxmin()) - 1]} (MAE {b.min():.1f}).")
    cm = ev["cm"]
    if cm[2].sum() > 0:
        rec = cm[2, 2] / cm[2].sum() * 100
        prec = cm[2, 2] / cm[:, 2].sum() * 100 if cm[:, 2].sum() else 0
        n_ts = f"{int(cm[2].sum()):,}".replace(",", ".")
        t.append(f"Dari <b>{n_ts}</b> hari berstatus Tidak sehat, model memperingatkan <b>{rec:.0f}%</b> "
                 f"(precision {prec:.0f}%).")
    else:
        t.append("Tidak ada hari berstatus Tidak sehat pada data evaluasi, sehingga peringatan dini untuk status "
                 "tertinggi belum bisa diuji.")
    return t


def model():
    uji, label_uji = data_uji()
    ev = evaluasi(tuple(pilih_kota))
    baseline = sumber == "baseline"
    intro("<b>Halaman ini menjawab:</b> seberapa bisa dipercaya prediksi AirGuard? Evaluasi memakai data uji "
          f"({label_uji}) yang tidak dipakai untuk melatih model, dan mengikuti filter wilayah di sidebar "
          "(filter tanggal tidak berlaku di sini).")
    if baseline:
        st.warning("Prediksi yang dievaluasi di sini adalah baseline persistence (besok = hari ini), bukan model tim. "
                   "Angkanya adalah batas bawah yang harus dikalahkan model.")

    with kotak("temuan"):
        st.subheader("Temuan utama")
        st.caption("Ringkasan yang dihitung otomatis dari data. Perlu dicek dan ditafsirkan oleh peneliti.")
        st.markdown("<ul>" + "".join(f"<li>{x}</li>" for x in temuan(ev)) + "</ul>", unsafe_allow_html=True)

    with st.expander("Arti istilah di halaman ini"):
        st.markdown(
            "- **MAE**: rata-rata selisih absolut prediksi dan kenyataan (µg/m³). Metrik utama, makin kecil makin baik.\n"
            "- **RMSE**: seperti MAE tetapi lebih menghukum kesalahan besar.\n"
            "- **R²**: porsi variasi PM2.5 yang dijelaskan model (maksimum 1).\n"
            "- **Bias**: rata-rata (prediksi − aktual). Positif berarti cenderung terlalu tinggi.\n"
            "- **Persistence**: tebakan sederhana bahwa PM2.5 besok sama dengan hari ini. Model hanya berguna kalau "
            "konsisten lebih baik dari ini.\n"
            "- **Recall status**: dari semua hari yang sebenarnya berstatus tertentu, berapa persen yang terdeteksi. "
            "Untuk peringatan dini, recall status Tidak sehat paling penting.\n"
            "- **Precision status**: dari semua hari yang diprediksi berstatus tertentu, berapa persen yang benar.\n"
            "- **Data training/validasi/testing**: latih 2022-2024, setel 2025, uji sejak 1 Jan 2026.")

    ket_mae = (f"vs persistence {ev['mae_pers']:.2f}" if not np.isnan(ev["mae_pers"]) and not baseline else "µg/m³")
    grid("g4",
         stat("MAE", f"{ev['mae']:.2f}", ket_mae, "tren", "#DCEBD8"),
         stat("RMSE", f"{ev['rmse']:.2f}", "µg/m³, lebih menghukum galat besar", "angin", "#E8F0C9"),
         stat("R²", f"{ev['r2']:.3f}", "makin dekat 1 makin baik", "daun", "#D5E8E4"),
         stat("Bias", f"{ev['bias']:+.2f}", "µg/m³, positif = terlalu tinggi", "awas", "#F8E7C4"))
    st.caption(f"Dihitung dari {ev['n']:,} pasangan prediksi dan nilai aktual pada data uji ({label_uji}).".replace(",", "."))

    cm = ev["cm"]
    benar = np.diag(cm).astype(float)
    rec_k = np.divide(benar, cm.sum(axis=1), out=np.full(3, np.nan), where=cm.sum(axis=1) > 0)
    pre_k = np.divide(benar, cm.sum(axis=0), out=np.full(3, np.nan), where=cm.sum(axis=0) > 0)
    f1_k = 2 * pre_k * rec_k / (pre_k + rec_k)
    st.subheader("Metrik status (3 kelas)")
    st.caption("Status adalah keluaran yang dilihat pengguna, jadi akurasinya dinilai terpisah dari galat PM2.5. "
               "Macro F1 adalah rata-rata F1 ketiga status, sehingga status yang jarang muncul tetap diperhitungkan.")
    fmt = lambda v: "–" if np.isnan(v) else f"{v * 100:.1f}%"
    grid("g4",
         stat("Akurasi status", f"{benar.sum() / cm.sum() * 100:.1f}%", "hari dengan status tepat", "pin", "#DCEBD8"),
         stat("Macro F1", "–" if np.isnan(f1_k).all() else f"{np.nanmean(f1_k):.3f}", "rata-rata F1 tiga status", "tren", "#E8F0C9"),
         stat("Recall Tidak sehat", fmt(rec_k[2]), "dari hari Tidak sehat yang terdeteksi", "awas", "#F8E7C4"),
         stat("Precision Tidak sehat", fmt(pre_k[2]), "dari peringatan yang benar", "angin", "#D5E8E4"))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("aktual"):
            st.subheader("Aktual vs prediksi")
            st.caption("Satu titik adalah satu hari di satu kabupaten/kota (sampel 1.500 titik). Makin dekat ke garis putus-putus, "
                       "makin tepat. Sebaran yang melebar di nilai tinggi berarti model kesulitan pada polusi tinggi.")
            e = ev["sebar"]
            fig3 = px.scatter(e, x="pm2_5_aktual", y="pm2_5_prediksi", color="provinsi", opacity=0.5,
                              color_discrete_map=WARNA_PROVINSI,
                              labels={"pm2_5_aktual": "Aktual (µg/m³)", "pm2_5_prediksi": "Prediksi (µg/m³)",
                                      "provinsi": "Provinsi"})
            mx = float(max(e["pm2_5_aktual"].max(), e["pm2_5_prediksi"].max()))
            fig3.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines", name="Prediksi = aktual",
                                      line=dict(color="#8A9A95", dash="dot")))
            st.plotly_chart(pakai_tema(fig3, 360))
    with kanan:
        with kotak("galat"):
            st.subheader("Sebaran galat")
            st.caption("Histogram prediksi dikurangi aktual. Puncak di nol yang simetris menandakan model tidak condong "
                       "ke satu arah. Ekor panjang di kanan berarti sesekali meleset jauh ke atas.")
            fig2 = go.Figure(go.Histogram(x=ev["sampel_e"], nbinsx=50, marker_color=WARNA_UTAMA, opacity=0.85))
            fig2.add_vline(x=0, line=dict(color=WARNA_KATEGORI["Tidak sehat"], dash="dash", width=1.2))
            fig2.update_xaxes(title="Prediksi − aktual (µg/m³)")
            fig2.update_yaxes(title="Jumlah hari")
            st.plotly_chart(pakai_tema(fig2, 360))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("galat_prov"):
            st.subheader("Galat per provinsi")
            st.caption("MAE tiap provinsi. Batang tua adalah provinsi yang paling sulit diprediksi.")
            g = ev["prov"]
            fig4 = go.Figure(go.Bar(x=g["provinsi"], y=g["MAE"], text=g["MAE"].round(1), textposition="outside",
                                    marker_color=[WARNA_UTAMA if v == g["MAE"].max() else "#B9D4CF" for v in g["MAE"]]))
            fig4.update_yaxes(title="MAE (µg/m³)", range=[0, float(g["MAE"].max()) * 1.2])
            st.plotly_chart(pakai_tema(fig4, 320))
    with kanan:
        with kotak("galat_bulan"):
            st.subheader("Galat per bulan")
            st.caption("MAE menurut bulan kalender. Batang tua adalah bulan yang paling sulit diprediksi.")
            b = ev["bulan"].reset_index()
            b.columns = ["bulan", "MAE"]
            b["nama"] = b["bulan"].map(lambda m: BULAN_PENDEK[int(m) - 1])
            fig5 = go.Figure(go.Bar(x=b["nama"], y=b["MAE"], text=b["MAE"].round(1), textposition="outside",
                                    marker_color=[WARNA_UTAMA if v == b["MAE"].max() else "#B9D4CF" for v in b["MAE"]]))
            fig5.update_yaxes(title="MAE (µg/m³)", range=[0, float(b["MAE"].max()) * 1.2])
            st.plotly_chart(pakai_tema(fig5, 320))

    with kotak("ews_eval"):
        st.subheader("Evaluasi status peringatan dini")
        st.caption("Status sebenarnya (baris) dibandingkan status prediksi (kolom). Diagonal adalah prediksi yang benar, "
                   "persentase dihitung per baris. Sel di bawah diagonal pada baris Tidak sehat adalah peringatan yang terlewat.")
        total = cm.sum(axis=1, keepdims=True)
        pct = np.divide(cm, total, out=np.zeros(cm.shape), where=total > 0) * 100
        teks = [[f"{cm[i, j]:,}".replace(",", ".") + f"<br>{pct[i, j]:.0f}%" for j in range(3)] for i in range(3)]
        k1, k2 = st.columns([1.2, 1], gap="large")
        with k1:
            fig6 = go.Figure(go.Heatmap(
                z=pct, x=NAMA_STATUS, y=NAMA_STATUS, zmin=0, zmax=100, showscale=False, xgap=3, ygap=3,
                colorscale=[[0, "#EEF3F0"], [1, "#6FB5A8"]], text=teks, texttemplate="%{text}",
                textfont=dict(size=13, color="#14231F"),
                hovertemplate="Sebenarnya %{y}, diprediksi %{x}<extra></extra>"))
            fig6.update_yaxes(autorange="reversed", title="Status sebenarnya")
            fig6.update_xaxes(side="top", title="Status prediksi")
            st.plotly_chart(pakai_tema(fig6, 330))
        with k2:
            tabel = pd.DataFrame({"Status": NAMA_STATUS, "Jumlah hari": cm.sum(axis=1),
                                  "Recall": rec_k * 100, "Precision": pre_k * 100, "F1": f1_k * 100})
            st.dataframe(tabel, hide_index=True, column_config={
                "Recall": st.column_config.NumberColumn(format="%.1f%%"),
                "Precision": st.column_config.NumberColumn(format="%.1f%%"),
                "F1": st.column_config.NumberColumn(format="%.1f%%")})
            st.caption(f"Akurasi status keseluruhan {np.trace(cm) / cm.sum() * 100:.1f}%. Status yang jarang terjadi mudah "
                       "terlihat bagus pada akurasi, jadi baca recall dan precision tiap status. Tanda – berarti status "
                       "itu tidak pernah muncul.")

    if metrik is None or fitur is None:
        st.info("Perbandingan model dan feature importance akan muncul di sini setelah tim menaruh model_metrics.csv dan "
                "feature_importance.csv di data/data_gabungan.")
        return
    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("metrik"):
            st.subheader("Perbandingan model (hasil evaluasi tim)")
            st.caption("Dari model_metrics.csv. Sel yang disorot hijau adalah nilai terbaik di kolomnya.")
            st.dataframe(
                metrik.style.format({"MAE": "{:.2f}", "RMSE": "{:.2f}", "R2": "{:.2f}"})
                .highlight_min(subset=["MAE", "RMSE"], color="#D7F0E8")
                .highlight_max(subset=["R2"], color="#D7F0E8"),
                hide_index=True, height=38 * (len(metrik) + 1) + 3)
            m = metrik.sort_values("MAE", ascending=False)
            fig7 = px.bar(m, x="MAE", y="model", orientation="h", color_discrete_sequence=[WARNA_UTAMA])
            fig7.update_yaxes(title=None)
            st.plotly_chart(pakai_tema(fig7, 240))
    with kanan:
        with kotak("fitur"):
            st.subheader("Fitur yang paling banyak digunakan model")
            st.caption("Batang lebih panjang berarti fitur itu lebih sering dipakai. Ini menunjukkan apa yang diandalkan "
                       "model, bukan penyebab polusi.")
            f = fitur.sort_values("importance").tail(10).copy()
            f["label"] = f["feature"].map(lambda x: LABEL_FITUR.get(x, x))
            fig8 = px.bar(f, x="importance", y="label", orientation="h", color_discrete_sequence=[WARNA_UTAMA])
            fig8.update_yaxes(title=None)
            fig8.update_xaxes(title="Feature importance")
            st.plotly_chart(pakai_tema(fig8, 420))


# ====================== PROYEKSI 2027 ======================
MUSIM = [(1, 3, "Hujan", "#DCE9F2"), (4, 5, "Pancaroba", "#EEF1EE"), (6, 9, "Kemarau", "#F6EBCB"),
         (10, 10, "Pancaroba", "#EEF1EE"), (11, 12, "Hujan", "#DCE9F2")]


def rentang_bulan(bulan):
    """[6,7,8] -> 'Juni sampai Agustus'; [5,9] -> 'Mei dan September'."""
    b = sorted(set(bulan))
    if not b:
        return ""
    grup, mulai = [], b[0]
    for a, c in zip(b, b[1:] + [None]):
        if c != a + 1:
            grup.append((mulai, a))
            mulai = c
    teks = [BULAN[m - 1] if m == a else f"{BULAN[m - 1]} sampai {BULAN[a - 1]}" for m, a in grup]
    return " dan ".join(teks) if len(teks) <= 2 else ", ".join(teks[:-1]) + " dan " + teks[-1]


@st.cache_data(show_spinner=False, max_entries=64)
def seri_proyeksi(level, nama):
    F = muat_proyeksi()[0]
    kolom = ["pm2_5_prakiraan", "batas_bawah", "batas_atas"]
    if level == "Provinsi":
        proj = F[F["provinsi"] == nama].groupby("tanggal")[kolom].mean().reset_index()
        h = pred[(pred["provinsi"] == nama) & pred["pm2_5_aktual"].notna()]
    else:
        proj = F[F["kota"] == nama][["tanggal", *kolom]]
        h = pred[(pred["kota"] == nama) & pred["pm2_5_aktual"].notna()]
    riwayat = h.groupby("tanggal_prediksi", observed=True)["pm2_5_aktual"].mean().reset_index().tail(120)
    return proj, riwayat


@st.cache_data(show_spinner=False)
def tabel_bulan(dasar):
    F, _, _, tahun = muat_proyeksi()
    x = F[F["tanggal"].dt.year == tahun].assign(bulan=lambda d: d["tanggal"].dt.month)
    return x.groupby([dasar, "bulan"])["pm2_5_prakiraan"].mean().unstack().reindex(columns=range(1, 13))


@st.cache_data(show_spinner=False)
def cakupan_provinsi():
    ada = set(pred["kota"].astype(str).unique())
    return {p: (sum(k in ada for k in WILAYAH.loc[WILAYAH["provinsi"] == p, "kota"]),
                int((WILAYAH["provinsi"] == p).sum())) for p in PROVINSI}


def rekomendasi(prov_bulan, tahun):
    saran = []
    status = pd.DataFrame(kode_status(prov_bulan.to_numpy()), index=prov_bulan.index, columns=prov_bulan.columns)
    bahaya = status.eq(2)
    if bahaya.to_numpy().any():
        rinci = "; ".join(f"{prov} pada {rentang_bulan([m for m in prov_bulan.columns if bahaya.loc[prov, m]])}"
                          for prov in prov_bulan.index if bahaya.loc[prov].any())
        saran.append(f"Pada {tahun}, rata-rata PM2.5 bulanan diproyeksikan melewati {BATAS_TINGGI:.0f} µg/m³ (status Tidak sehat) di: "
                     f"<b>{rinci}</b>. Siapkan razia emisi kendaraan bermotor dan pengendalian pembakaran terbuka sebelum bulan itu, "
                     "serta pertimbangkan WFH parsial dan perluasan Car Free Day pada puncaknya.")
    else:
        rata = prov_bulan.mean()
        puncak = [int(m) for m in rata.sort_values(ascending=False).head(3).index]
        p_top = prov_bulan.stack().idxmax()
        saran.append(f"Tidak ada provinsi yang diproyeksikan melewati {BATAS_TINGGI:.0f} µg/m³ pada rata-rata bulanan. "
                     f"Puncak proyeksi ada di <b>{rentang_bulan(puncak)}</b> ({p_top[0]}, bulan {BULAN[int(p_top[1]) - 1]} "
                     f"sekitar {prov_bulan.stack().max():.0f} µg/m³). Siapkan kampanye pengurangan emisi sebelum bulan-bulan itu.")
    sedang = [m for m in prov_bulan.columns if (status[m] >= 1).sum() >= max(3, len(prov_bulan) // 2)]
    if sedang and len(sedang) < 12:
        saran.append(f"<b>{rentang_bulan(sedang)}</b>: sedikitnya setengah provinsi berstatus Sedang atau lebih tinggi. "
                     "Perkuat edukasi untuk kelompok sensitif dan siagakan layanan kesehatan pernapasan.")
    kurang = [(p, a, b) for p, (a, b) in cakupan_provinsi().items() if a < b]
    if kurang:
        saran.append("Lengkapi cakupan data dan pemantauan di " + "; ".join(
            f"{p} (baru {a} dari {b} kabupaten/kota)" for p, a, b in kurang) + ".")
    else:
        saran.append("Cakupan data sudah lengkap untuk seluruh kabupaten/kota. Pertahankan kesinambungan pemantauan.")
    return saran


def proyeksi():
    F, metode, akhir, tahun = muat_proyeksi()
    intro(f"<b>Halaman ini menjawab:</b> kapan polusi cenderung tinggi sepanjang {tahun}? Rentang proyeksi: "
          f"{(akhir + pd.Timedelta(days=1)):%d %b %Y} sampai 31 Des {tahun}. Metode: "
          + ("pola musiman historis" if metode == "musiman" else "prakiraan dari model tim") + ".")
    if metode == "musiman":
        st.info(f"Proyeksi ini dihitung dari pola musiman rata-rata data {pre['tanggal'].min():%b %Y} sampai "
                f"{pre['tanggal'].max():%b %Y}, bukan dari model machine learning. Artinya ia menggambarkan bulan-bulan yang "
                "cenderung tinggi, bukan ramalan harian, dan belum memperhitungkan tren jangka panjang, perubahan kebijakan, "
                "atau kejadian khusus seperti kebakaran lahan. Untuk besok hari, lihat tab Ringkasan.")

    pb0 = tabel_bulan("provinsi").reindex(PROVINSI).dropna(how="all")
    puncak = pb0.stack()
    (p_prov, p_bln), p_val = puncak.idxmax(), puncak.max()
    rata_bln = pb0.mean()
    bln_top = int(rata_bln.idxmax())
    rata_prov = pb0.mean(axis=1)
    n_bahaya = int((pb0.to_numpy() > BATAS_TINGGI).any(axis=1).sum())
    grid("g4",
         stat("Puncak proyeksi bulanan", f"{p_val:.0f} µg/m³", f"{p_prov}, {BULAN[int(p_bln) - 1]}", "awas", "#F8E7C4"),
         stat("Bulan paling berisiko", BULAN[bln_top - 1], f"rata-rata {rata_bln.max():.0f} µg/m³ di semua provinsi", "tren", "#E8F0C9"),
         stat("Provinsi paling berisiko", rata_prov.idxmax(), f"rata-rata setahun {rata_prov.max():.0f} µg/m³", "pin", "#DCEBD8"),
         stat("Provinsi melewati batas", f"{n_bahaya} dari {len(pb0)}", f"punya bulan di atas {BATAS_TINGGI:.0f} µg/m³", "angin", "#D5E8E4"))

    with kotak("tren_proyeksi"):
        st.subheader("Tren PM2.5 jangka panjang")
        c1, c2, _ = st.columns([1.3, 1.6, 1.4])
        level = c1.radio("Lihat per", ["Provinsi", "Kabupaten/kota"], horizontal=True, key="prj_level")
        if level == "Provinsi":
            nama = c2.selectbox("Provinsi", [p for p in PROVINSI if p in set(F["provinsi"].astype(str))] or PROVINSI, key="prj_prov")
        else:
            opsi = sorted(F["kota"].unique())
            nama = c2.selectbox("Kabupaten/kota", opsi, index=daerah_awal(opsi), key="prj_kota", help="Ketik untuk mencari nama.")
        proj, riwayat = seri_proyeksi(level, nama)
        st.caption("Garis abu-abu adalah data aktual 120 hari terakhir. Garis hijau tua adalah proyeksi, dengan pita hijau muda "
                   "sebagai rentang harian yang wajar (± satu simpangan baku). Garis merah putus-putus adalah batas Tidak sehat. "
                   "Warna latar menandai pola musim secara umum.")
        if proj.empty:
            st.info("Belum ada data proyeksi untuk pilihan ini.")
        else:
            x0 = riwayat["tanggal_prediksi"].min() if not riwayat.empty else proj["tanggal"].min()
            x1 = proj["tanggal"].max()
            fig = go.Figure()
            label_terakhir = None
            for th in range(x0.year, x1.year + 1):
                for a, b, label, warna in MUSIM:
                    s, e = pd.Timestamp(th, a, 1), pd.Timestamp(th, b, 1) + pd.offsets.MonthEnd(0)
                    s, e = max(s, x0), min(e, x1)
                    if s < e:
                        tampil = label if (label != label_terakhir and (e - s).days > 40) else ""
                        fig.add_vrect(x0=s, x1=e, fillcolor=warna, opacity=0.6, line_width=0, layer="below",
                                      annotation_text=tampil, annotation_position="top left",
                                      annotation_font=dict(size=10, color="#5A6B66"))
                        label_terakhir = label
            fig.add_trace(go.Scatter(x=proj["tanggal"], y=proj["batas_atas"], mode="lines", line=dict(width=0),
                                     showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=proj["tanggal"], y=proj["batas_bawah"], mode="lines", line=dict(width=0), fill="tonexty",
                                     fillcolor="rgba(15,92,85,0.15)", name="Rentang harian wajar", hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=riwayat["tanggal_prediksi"], y=riwayat["pm2_5_aktual"], name="Aktual",
                                     line=dict(color="#8A9A95", width=1.6)))
            fig.add_trace(go.Scatter(x=proj["tanggal"], y=proj["pm2_5_prakiraan"], name="Proyeksi",
                                     line=dict(color=WARNA_UTAMA, width=2.2)))
            fig.add_hline(y=BATAS_TINGGI, line=dict(color=WARNA_KATEGORI["Tidak sehat"], width=1.2, dash="dash"),
                          annotation_text=f"Batas Tidak sehat {BATAS_TINGGI:.0f}", annotation_position="top right",
                          annotation_font=dict(size=11, color=WARNA_KATEGORI["Tidak sehat"]))
            tinggi_maks = np.nanmax([proj["batas_atas"].max(), proj["pm2_5_prakiraan"].max(), riwayat["pm2_5_aktual"].max()])
            fig.update_yaxes(title="PM2.5 (µg/m³)", range=[0, max(BATAS_TINGGI + 10, float(tinggi_maks) * 1.1)])
            st.plotly_chart(pakai_tema(fig, 400))

    with kotak("kalender"):
        st.subheader(f"Kalender risiko polusi {tahun}")
        st.caption("Setiap kotak adalah rata-rata proyeksi PM2.5 bulan itu, diwarnai menurut status. "
                   "Dipakai untuk melihat bulan mana yang paling perlu diwaspadai.")
        mode = st.radio("Baris", ["Provinsi", "Kabupaten/kota pilihan"], horizontal=True, key="prj_heat")
        if mode == "Provinsi":
            m = tabel_bulan("provinsi").reindex(PROVINSI).dropna(how="all")
            label = list(m.index)
        else:
            kandidat_h = sorted(F["kota"].unique())
            awal_h = sorted([k for k in kandidat_h if TIPE_DARI_KOTA[k] == "Kota"], key=lambda k: -PENDUDUK[k])[:8]
            pilih_h = st.multiselect("Kabupaten/kota", kandidat_h, default=awal_h, key="prj_heat_kota")
            m = tabel_bulan("kota").reindex(pilih_h or awal_h)
            label = list(m.index)
        z = kode_status(m.to_numpy())
        w = [k[2] for k in KATEGORI]
        fig2 = go.Figure(go.Heatmap(
            z=z, x=BULAN_PENDEK, y=label, zmin=0, zmax=2, showscale=False, xgap=3, ygap=3,
            colorscale=[[0, w[0]], [0.25, w[0]], [0.25, w[1]], [0.75, w[1]], [0.75, w[2]], [1, w[2]]],
            text=np.round(m.to_numpy()).astype(int).astype(str), texttemplate="%{text}",
            textfont=dict(size=12, color="#14231F"),
            hovertemplate="%{y}, %{x}: %{text} µg/m³<extra></extra>"))
        fig2.update_yaxes(autorange="reversed")
        fig2.update_xaxes(side="top")
        st.plotly_chart(pakai_tema(fig2, 130 + 44 * len(label)))
        st.markdown(legenda_kategori(), unsafe_allow_html=True)
        st.caption("Angka di kotak: rata-rata PM2.5 bulanan (µg/m³).")

    pb = tabel_bulan("provinsi").reindex(PROVINSI).dropna(how="all")
    with kotak("rekomendasi"):
        st.subheader("Rekomendasi kebijakan daerah")
        st.caption("Dihasilkan otomatis dari angka proyeksi di atas, sebagai bahan diskusi. Bukan keputusan kebijakan.")
        st.markdown("<ol>" + "".join(f"<li>{s}</li>" for s in rekomendasi(pb, tahun)) + "</ol>", unsafe_allow_html=True)
        unduh = pb.copy()
        unduh.columns = BULAN
        st.download_button("Unduh proyeksi bulanan per provinsi (CSV)", unduh.round(1).to_csv().encode("utf-8"),
                           file_name=f"airguard_proyeksi_{tahun}.csv", mime="text/csv")


# ====================== KLASTER WILAYAH ======================
def klaster():
    k = muat_cluster_rinci()
    intro("<b>Halaman ini menjawab:</b> daerah mana yang punya pola polusi serupa? Kabupaten/kota dikelompokkan dengan K-Means "
          "(k=3) dari rata-rata PM2.5, persentase hari tinggi, serta jumlah dan lama episode. Zona bersifat tetap per wilayah "
          "dan tidak berubah menurut tanggal. Petanya ada di tab Ringkasan, mode \"Zona cluster\".")
    if k is None:
        st.info("Hasil clustering belum ada di `data/data_gabungan/clustering_wilayah.csv`. "
                "Jalankan notebooks/04_modeling/CLUSTERING.ipynb lebih dulu.")
        return
    k = k[k["kota"].isin(pilih_kota)]
    if k.empty:
        st.info("Tidak ada wilayah berklaster pada filter ini.")
        return
    ikon_zona = {"rendah-stabil": "daun", "sedang-musiman": "angin", "tinggi-persisten": "awas"}
    pastel = {"rendah-stabil": "#DCEBD8", "sedang-musiman": "#F8E7C4", "tinggi-persisten": "#F4D5D1"}
    ringkas = (k.groupby("zona").agg(Wilayah=("kota", "size"), Rata=("rata_rata_pm25", "mean"),
                                     Hari=("persentase_hari_tinggi", "mean"))
               .reindex(URUTAN_ZONA).dropna(how="all"))
    kartu_z = [stat(LABEL_ZONA.get(z, z), f"{int(r['Wilayah'])} wilayah",
                    f"rata-rata {r['Rata']:.1f} µg/m³, {r['Hari']:.0f}% hari tinggi", ikon_zona.get(z, "pin"), pastel.get(z, "#D5E8E4"))
               for z, r in ringkas.iterrows()]
    grid("g3", *kartu_z)

    prof = profil_unik(pre)
    if prof["n_unik"] < prof["n_kota"]:
        st.caption(f"Catatan data: dari {prof['n_kota']} wilayah hanya ada {prof['n_unik']} deret PM2.5 yang berbeda. "
                   "Wilayah yang berdekatan (misalnya Jakarta Selatan, Jakarta Timur, Depok, dan Bekasi) jatuh pada sel grid "
                   "sumber data yang sama, sehingga nilainya identik dan sering masuk zona yang sama.")

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("klaster_sebar"):
            st.subheader("Rata-rata PM2.5 dan hari tinggi")
            st.caption("Satu titik satu kabupaten/kota. Ke kanan atas berarti rata-rata tinggi dan sering melewati ambang.")
            fig = px.scatter(k, x="rata_rata_pm25", y="persentase_hari_tinggi", color="zona", hover_name="kota",
                             color_discrete_map=WARNA_ZONA, category_orders={"zona": URUTAN_ZONA},
                             labels={"rata_rata_pm25": "Rata-rata PM2.5 (µg/m³)", "persentase_hari_tinggi": "Hari tinggi (%)",
                                     "zona": "Zona"})
            fig.for_each_trace(lambda t: t.update(name=LABEL_ZONA.get(t.name, t.name)))
            st.plotly_chart(pakai_tema(fig, 380))
    with kanan:
        with kotak("klaster_prov"):
            st.subheader("Zona per provinsi")
            st.caption("Jumlah kabupaten/kota di tiap zona.")
            p = k.groupby(["provinsi", "zona"], as_index=False).size()
            fig2 = px.bar(p, x="size", y="provinsi", color="zona", orientation="h", color_discrete_map=WARNA_ZONA,
                          category_orders={"zona": URUTAN_ZONA}, labels={"size": "Wilayah", "provinsi": "", "zona": "Zona"})
            fig2.for_each_trace(lambda t: t.update(name=LABEL_ZONA.get(t.name, t.name)))
            st.plotly_chart(pakai_tema(fig2, 380))
    with kotak("klaster_tabel"):
        st.subheader("Daftar wilayah")
        kol = [c for c in ["kota", "provinsi", "zona", "rata_rata_pm25", "persentase_hari_tinggi", "jumlah_episode",
                           "durasi_episode_terpanjang"] if c in k.columns]
        t = k.sort_values("rata_rata_pm25", ascending=False)[kol].assign(zona=lambda d: d["zona"].map(lambda z: LABEL_ZONA.get(z, z)))
        st.dataframe(t, hide_index=True, height=360, column_config={
            "kota": "Kabupaten/kota", "provinsi": "Provinsi", "zona": "Zona",
            "rata_rata_pm25": st.column_config.NumberColumn("Rata-rata PM2.5", format="%.1f"),
            "persentase_hari_tinggi": st.column_config.NumberColumn("Hari tinggi (%)", format="%.1f"),
            "jumlah_episode": "Jumlah episode", "durasi_episode_terpanjang": "Episode terpanjang (hari)"})


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

# Halaman dashboard memakai kontainer lebih lebar supaya tidak ada pita kosong di layar besar.
st.markdown("<style>.block-container {max-width: min(1560px, 94vw);}</style>", unsafe_allow_html=True)

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

st.sidebar.caption("Status: Baik sampai 15, Sedang 15,1 sampai 55, Tidak sehat di atas 55 µg/m³. Ini aturan visualisasi proyek, bukan klaim medis.")

if sumber != "tim":
    st.sidebar.warning(catatan_sumber())

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
tab_ringkasan, tab_tren, tab_proy, tab_cuaca, tab_klaster, tab_model = st.tabs(
    ["Ringkasan", "Tren & Prediksi", f"Proyeksi {tgl_aktual.max().year + 1}", "Faktor Lain", "Klaster wilayah", "Model"],
    key="tab_dash", on_change="rerun")
for tab, fungsi in [(tab_ringkasan, ringkasan), (tab_tren, tren), (tab_proy, proyeksi), (tab_cuaca, cuaca),
                    (tab_klaster, klaster), (tab_model, model)]:
    with tab:
        if tab.open:
            butuh_kota(fungsi)
