"""Tema dan komponen tampilan dashboard EWS (palet biru tua)."""
import streamlit as st

from data import EWS

BIRU = "#1E3A8A"
TEKS = "#0F172A"
TEKS_PUDAR = "#475569"
GARIS = "#E2E8F0"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root {--biru:#1E3A8A; --biru2:#2E4FA8; --teks:#0F172A; --pudar:#475569; --garis:#E2E8F0; --latar:#F8FAFC;}
.stApp {background: var(--latar);}
.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp button {font-family: 'Inter', sans-serif;}
.block-container {max-width: 1280px; padding-top: 3.4rem; padding-bottom: 4rem;}
[data-testid="stVerticalBlock"] {gap: 1.2rem;}
[data-testid="stHeader"] {background: #FFFFFF; border-bottom: 1px solid var(--garis);}
.stApp h3 {font-size: 1.08rem !important; font-weight: 600 !important; color: var(--teks); padding: .3rem 0 .1rem !important;}
[class*="st-key-card_"] h3 {padding-top: 0 !important;}

/* ---- navigasi atas ---- */
[data-testid="stHeader"] a, [data-testid="stHeader"] button p, [data-testid="stHeader"] [role="tab"] {
    font-family: 'Inter', sans-serif !important; font-weight: 500;}

[data-testid="stTopNav"] {position: absolute; left: 1.2rem; right: 9rem; width: auto !important; gap: 10px;
    justify-content: stretch !important; flex-wrap: nowrap;}
[data-testid="stTopNav"] .rc-overflow-item {flex: 1 1 0 !important; min-width: 0;}
[data-testid="stTopNav"] [data-testid="stTopNavLinkContainer"], [data-testid="stTopNav"] [data-testid="stTopNavLink"] {
    width: 100% !important; justify-content: center; text-align: center;}
[data-testid="stTopNav"] [data-testid="stTopNavLinkContainer"] {height: auto !important;}
[data-testid="stTopNav"] [data-testid="stTopNavLink"] {background: #FFFFFF !important; border: 1px solid var(--garis);
    border-radius: 10px !important; padding: .5rem 1rem !important; height: auto !important; font-weight: 600; color: var(--pudar) !important;}
[data-testid="stTopNav"] [data-testid="stTopNavLink"]:hover {background: #EEF2FF !important; border-color: #C7D2FE;}
[data-testid="stTopNav"] [data-testid="stTopNavLink"][aria-current="page"] {background: var(--biru) !important; border-color: var(--biru);
    color: #FFFFFF !important;}
[data-testid="stTopNav"] [data-testid="stTopNavLink"][aria-current="page"] * {color: #FFFFFF !important;}

/* ---- kartu ---- */
[class*="st-key-card_"], .kartu {
    background: #FFFFFF; border: 1px solid var(--garis); border-radius: 14px; padding: 18px 20px;
    box-shadow: 0 1px 2px rgba(15,23,42,.04);
}
.kartu.flat {border: none; box-shadow: none; padding: 0; background: none;}
.grid {display: grid; gap: 16px; align-items: stretch; margin: .4rem 0 1.2rem;}
.g2 {grid-template-columns: repeat(2, minmax(0, 1fr));}
.g3 {grid-template-columns: repeat(3, minmax(0, 1fr));}
.g4 {grid-template-columns: repeat(4, minmax(0, 1fr));}
.g6 {grid-template-columns: repeat(6, minmax(0, 1fr));}
@media (max-width: 1000px) {.g4, .g6 {grid-template-columns: repeat(2, minmax(0, 1fr));} .g3 {grid-template-columns: 1fr;}}
.jud {font-weight: 600; font-size: .95rem; margin-bottom: 6px; color: var(--teks);}
.isi {font-size: .9rem; line-height: 1.55; color: var(--pudar);}
.stat .atas {display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;}
.stat .lab {font-size: .82rem; color: var(--pudar);}
.stat .ic {width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center;
    background: #E0E7FF; color: var(--biru); flex: none;}
.stat .ic svg {width: 19px; height: 19px;}
.stat .val {font-size: 1.8rem; font-weight: 700; margin: 6px 0 2px; color: var(--teks);}
.stat .ket {font-size: .82rem; color: var(--pudar);}
.stat.sb {border-left: 5px solid var(--sb);}
.intro {background: #EEF2FF; border: 1px solid #DDE5FB; border-radius: 12px; padding: 14px 18px; font-size: .93rem;
    line-height: 1.6; color: var(--teks);}
.intro {margin-bottom: .8rem;}
.kepala {margin-bottom: 1rem !important;}
.catatan {font-size: .8rem; color: var(--pudar); line-height: 1.5;}

/* ---- hero & judul halaman ---- */
.st-key-hero {background: var(--biru);}
.st-key-hero .eyebrow {font-size: .78rem; font-weight: 600; letter-spacing: .08em; color: #BFD0FF !important;}
.st-key-hero h1 {font-size: 2.35rem; line-height: 1.2; margin: .5rem 0 1rem; padding: 0; color: #FFFFFF !important; max-width: 860px;}
.st-key-hero .lead {font-size: 1.05rem; line-height: 1.65; max-width: 780px; color: #DCE6FF !important; margin: 0 0 20px;}
.st-key-hero button {border-radius: 10px !important; padding: .65rem 1.4rem !important; min-height: 3rem; font-weight: 600;}
.st-key-hero .st-key-btn_ews button {background: #FFFFFF !important; border: none !important;}
.st-key-hero .st-key-btn_ews button p {color: var(--biru) !important; font-weight: 600 !important;}
.st-key-hero .st-key-btn_proyeksi button, .st-key-hero .st-key-btn_analitik button {background: transparent !important; border: 1px solid #93AEEB !important;}
.st-key-hero .st-key-btn_proyeksi button p, .st-key-hero .st-key-btn_analitik button p {color: #FFFFFF !important; font-weight: 600 !important;}
.st-key-hero .st-key-btn_proyeksi button:hover, .st-key-hero .st-key-btn_analitik button:hover {background: rgba(255,255,255,.1) !important;}
.kepala {display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap;
    border-bottom: 1px solid var(--garis); padding-bottom: 14px; margin-bottom: .4rem;}
.kepala .jh {font-size: 1.6rem; font-weight: 700; color: var(--teks); margin: 0;}
.kepala .sh {font-size: .92rem; color: var(--pudar); margin-top: 2px;}
.chip {display: inline-block; font-size: .8rem; color: var(--biru); background: #E0E7FF; border-radius: 99px;
    padding: 4px 12px; margin: 0 6px 6px 0; font-weight: 500;}
.chipsdg {display: inline-block; font-size: .75rem; font-weight: 700; padding: 3px 10px; border-radius: 6px;
    background: var(--biru); color: #FFFFFF; margin-bottom: 10px;}

/* ---- status EWS ---- */
.pill {display: inline-block; font-size: .85rem; font-weight: 600; padding: 4px 12px; border-radius: 99px;}
.pill.besar {font-size: 1rem; padding: 6px 16px;}
.angka {font-size: 2.6rem; font-weight: 700; line-height: 1.1; margin: 6px 0 4px; color: var(--teks);}
.angka small {font-size: 1rem; font-weight: 500; color: var(--pudar);}
.kota-strip {border-top: 4px solid var(--sb);}
.kota-strip .nm {font-size: .85rem; color: var(--pudar); margin-bottom: 4px;}
.kota-strip .vl {font-size: 1.35rem; font-weight: 700; color: var(--teks); margin-bottom: 6px;}
.rek {margin: 8px 0 1.2rem; padding-left: 1.1rem; color: var(--pudar); font-size: .9rem; line-height: 1.6;}
.rek li {margin-bottom: 4px;}
.kv {display: flex; justify-content: space-between; font-size: .9rem; padding: 7px 0; border-top: 1px solid var(--garis); color: var(--pudar);}
.kv b {color: var(--teks); font-weight: 600;}

/* ---- tombol dan widget (menimpa tema bawaan dari config repo) ---- */
[data-testid="stRadioOption"][data-selected] > div > div:first-child {background: var(--biru) !important; border-color: var(--biru) !important;}
[data-testid="stMultiSelect"] [data-tag] {background: var(--biru) !important;}
[data-testid="stMultiSelect"] [data-tag] * {color: #FFFFFF !important;}
/* ---- tab di dalam halaman (bukan navigasi atas) ---- */
.block-container [data-testid="stTab"] {background: #FFFFFF; border: 1px solid var(--garis); border-radius: 10px;
    padding: .5rem 1.1rem; margin-right: 8px;}
.block-container [data-testid="stTab"] p {font-weight: 600; color: var(--pudar);}
.block-container [data-testid="stTab"][data-selected] {background: var(--biru); border-color: var(--biru);}
.block-container [data-testid="stTab"][data-selected] p {color: #FFFFFF !important;}
.block-container .react-aria-SelectionIndicator {display: none !important;}
.block-container [role="tablist"]::after {display: none !important;}
.block-container [role="tablist"] {gap: 0; border-bottom: none;}
.stDownloadButton button {border: 1px solid var(--biru) !important; background: #FFFFFF !important; border-radius: 10px !important;}
.stDownloadButton button p {color: var(--biru) !important; font-weight: 600 !important;}
.stDownloadButton button:hover {background: #EEF2FF !important;}

/* ---- penyegaran tampilan ---- */
.stApp {background: #F3F5FA;}
[class*="st-key-card_"], .kartu {border-radius: 18px; border-color: #E3E8F2; box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 8px 24px -12px rgba(15,23,42,.10);}
.kepala .jh {font-size: 2rem; letter-spacing: -.01em;}
.stat .val {font-size: 2.3rem; letter-spacing: -.02em;}
.angka {font-size: 3.2rem; letter-spacing: -.02em;}

/* kartu gelap untuk bagian wawasan utama */
.st-key-card_detail, .st-key-card_temuan, .st-key-card_rekomendasi, .kartu.gelap {background: #0F172A !important; border-color: #0F172A !important; color: #E2E8F0;}
.st-key-card_detail h3, .st-key-card_temuan h3, .st-key-card_rekomendasi h3, .kartu.gelap .jud {color: #FFFFFF !important;}
.st-key-card_detail p, .st-key-card_temuan p, .st-key-card_rekomendasi p, .st-key-card_detail li, .st-key-card_temuan li,
.st-key-card_rekomendasi li, .kartu.gelap .isi {color: #CBD5E1 !important;}
.st-key-card_detail [data-testid="stCaptionContainer"], .st-key-card_temuan [data-testid="stCaptionContainer"],
.st-key-card_rekomendasi [data-testid="stCaptionContainer"], .st-key-card_detail .catatan {color: #94A3B8 !important;}
.st-key-card_detail .jud, .st-key-card_detail .angka, .st-key-card_detail .kv b {color: #FFFFFF !important;}
.st-key-card_detail .angka small, .st-key-card_detail .kv {color: #94A3B8 !important;}
.st-key-card_detail .kv {border-top-color: rgba(255,255,255,.12);}
.st-key-card_temuan b, .st-key-card_rekomendasi b {color: #FFFFFF;}
.st-key-card_rekomendasi .stDownloadButton button {background: transparent !important; border: 1px solid #64748B !important;}
.st-key-card_rekomendasi .stDownloadButton button p {color: #FFFFFF !important;}
.st-key-card_rekomendasi .stDownloadButton button:hover {background: rgba(255,255,255,.08) !important;}

/* ---- landing ---- */
.st-key-hero {background: #1E3A8A; border-radius: 26px; padding: 54px 56px; overflow: hidden;}
.st-key-hero h1 {font-size: 2.7rem !important; letter-spacing: -.02em; line-height: 1.12 !important;}
.panel {background: #0B1226; border-radius: 22px; padding: 22px 24px; color: #E2E8F0; box-shadow: 0 20px 40px -20px rgba(0,0,0,.5);}
.panel .ph {display: flex; justify-content: space-between; font-size: .78rem; color: #94A3B8; margin-bottom: 14px;}
.panel .tiga {display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 18px;}
.panel .tg {background: #131C36; border-radius: 14px; padding: 12px 14px;}
.panel .tg .n {font-size: 2rem; font-weight: 700; color: #FFFFFF; line-height: 1.1;}
.panel .tg .l {font-size: .75rem; color: #94A3B8; margin-top: 4px;}
.panel .tg .t {display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px;}
.panel .bar {display: grid; grid-template-columns: 1fr 1.2fr auto; gap: 12px; align-items: center; padding: 8px 0;
    border-top: 1px solid rgba(255,255,255,.08); font-size: .88rem;}
.panel .bar .tr {height: 8px; border-radius: 99px; background: #1E293B; overflow: hidden;}
.panel .bar .tr i {display: block; height: 100%; border-radius: 99px;}
.panel .bar b {color: #FFFFFF; font-weight: 600;}
.panel .judulp {font-size: .78rem; color: #94A3B8; margin: 2px 0 2px;}
.angkabesar {display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0; background: #FFFFFF; border: 1px solid #E3E8F2;
    border-radius: 20px; margin: 1.4rem 0 .6rem; box-shadow: 0 8px 24px -12px rgba(15,23,42,.10);}
.angkabesar > div {padding: 26px 28px; border-left: 1px solid #E3E8F2;}
.angkabesar > div:first-child {border-left: none;}
.angkabesar .n {font-size: 2.6rem; font-weight: 700; letter-spacing: -.02em; color: #1E3A8A; line-height: 1.1;}
.angkabesar .n small {font-size: 1rem; font-weight: 500; color: #475569; margin-left: 4px;}
.angkabesar .l {font-size: .85rem; color: #475569; margin-top: 6px; line-height: 1.45;}
@media (max-width: 1000px) {.angkabesar {grid-template-columns: repeat(2, 1fr);} .angkabesar > div:nth-child(3) {border-left: none;}}
.sdgno {font-size: 3rem; font-weight: 700; color: #1E3A8A; line-height: 1; letter-spacing: -.03em; margin-bottom: 8px;}
.sdgno small {font-size: .85rem; font-weight: 600; color: #475569; letter-spacing: 0; margin-left: 6px;}
.kartu.lembut {background: #E8EEFC; border-color: #D5DFF7; box-shadow: none;}
.noc {font-size: .8rem; font-weight: 700; letter-spacing: .08em; color: #93B4F0; margin-bottom: 14px;}
.kartu.gelap .noc {color: #7FA2EA;}
.kartu.putih .noc {color: #1E3A8A;}
.bagian {font-size: 1.35rem; font-weight: 700; letter-spacing: -.01em; color: #0F172A; margin: 2rem 0 .2rem;}
.bagian + .sub {font-size: .92rem; color: #475569; margin-bottom: .9rem;}
.kartu, .panel, .angkabesar, .bagian, .sub, .catatan, .intro, .kepala, .rek {font-family: 'Inter', sans-serif;}

/* ---- sidebar gelap ---- */
[data-testid="stHeader"] {background: transparent !important; border-bottom: none !important;}
[data-testid="stSidebar"] {background: #0B1226 !important; border-right: none;}
[data-testid="stSidebar"] > div {background: #0B1226;}
[data-testid="stSidebarHeader"] {padding: 1.4rem 1rem .8rem;}
[data-testid="stSidebarNav"] {padding: .4rem .6rem;}
[data-testid="stSidebarNavLink"] {border-radius: 12px !important; padding: .65rem .9rem !important; margin-bottom: 4px; color: #CBD5E1 !important;}
[data-testid="stSidebarNavLink"] span, [data-testid="stSidebarNavLink"] p {color: #CBD5E1 !important; font-weight: 500;}
[data-testid="stSidebarNavLink"]:hover {background: rgba(255,255,255,.07) !important;}
[data-testid="stSidebarNavLink"][aria-current="page"] {background: #2E4FA8 !important;}
[data-testid="stSidebarNavLink"][aria-current="page"] span, [data-testid="stSidebarNavLink"][aria-current="page"] p {color: #FFFFFF !important; font-weight: 600;}
[data-testid="stSidebarUserContent"] {padding: 1rem 1.1rem 1.4rem;}
.sb-info {background: #131C36; border-radius: 14px; padding: 14px 16px; font-size: .8rem; line-height: 1.55; color: #94A3B8; margin-bottom: 10px;}
.sb-info b {color: #FFFFFF; font-size: .85rem;}
[data-testid="stSidebar"] .stButton button {background: transparent !important; border: 1px solid #334155 !important; border-radius: 12px !important;}
[data-testid="stSidebar"] .stButton button p {color: #E2E8F0 !important; font-weight: 600;}
[data-testid="stSidebar"] .stButton button:hover {background: rgba(255,255,255,.07) !important;}
.stat.gelap {background: #0F172A !important; border-color: #0F172A !important;}
.stat.gelap .lab, .stat.gelap .ket {color: #94A3B8;}
.stat.gelap .val {color: #FFFFFF;}
.stat.gelap .ic {background: rgba(255,255,255,.1); color: #FFFFFF;}
.delta {display: inline-block; font-size: .75rem; font-weight: 600; padding: 2px 8px; border-radius: 99px; margin-right: 6px;}
.delta.baik {background: #D1FAE5; color: #065F46;} .delta.buruk {background: #FEE2E2; color: #991B1B;} .delta.netral {background: #E2E8F0; color: #334155;}
.stat.gelap .delta.baik {background: rgba(16,185,129,.2); color: #6EE7B7;} .stat.gelap .delta.buruk {background: rgba(239,68,68,.22); color: #FCA5A5;}
.tabelk {width: 100%; border-collapse: collapse; font-size: .9rem;}
.tabelk th {text-align: left; font-weight: 500; font-size: .78rem; color: #64748B; padding: 8px 10px; border-bottom: 1px solid #E3E8F2;}
.tabelk td {padding: 11px 10px; border-bottom: 1px solid #EEF1F7; color: #0F172A;}
.tabelk tr:last-child td {border-bottom: none;}
.tabelk .n {text-align: right; font-variant-numeric: tabular-nums;}
.tabelk .mini {display: inline-block; width: 90px; height: 7px; border-radius: 99px; background: #E8EDF7; vertical-align: middle; margin-left: 10px; overflow: hidden;}
.tabelk .mini i {display: block; height: 100%; border-radius: 99px;}
.tabelk .no {color: #94A3B8; width: 28px;}
.stat .ket .delta {display: table; margin: 0 0 6px;}
.tabelk, .tabelk th, .tabelk td {border-left: none !important; border-right: none !important; border-top: none !important;}
.tabelk {border: none !important;}
.tabelk th {background: transparent !important;}
.stat .val.kecil {font-size: 1.75rem; line-height: 1.25; margin: 10px 0 6px;}
</style>
"""


def pasang_css():
    st.markdown(CSS, unsafe_allow_html=True)


_SV = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
       'stroke-linecap="round" stroke-linejoin="round">{}</svg>')
IKON = {
    "pin": _SV.format('<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>'),
    "grafik": _SV.format('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'),
    "target": _SV.format('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>'),
    "orang": _SV.format('<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 3-6 6.5-6s6.5 2.4 6.5 6M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20c0-2.8-1.6-4.7-4-5.5"/>'),
    "awas": _SV.format('<path d="M12 3l10 18H2L12 3zM12 10v5M12 18v.5"/>'),
    "tren": _SV.format('<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>'),
}


def kartu(judul, isi, atas="", kelas=""):
    return f'<div class="kartu {kelas}">{atas}<div class="jud">{judul}</div><div class="isi">{isi}</div></div>'


def stat(label, nilai, ket, ikon, warna=None, gelap=False, delta=None):
    """delta = (teks, "baik"|"buruk"|"netral") ditampilkan sebagai lencana kecil di baris keterangan."""
    gaya = f' style="--sb:{warna}"' if warna else ""
    kelas = "stat" + (" sb" if warna else "") + (" gelap" if gelap else "")
    kls = " kecil" if len(str(nilai)) > 9 else ""
    d = f'<span class="delta {delta[1]}">{delta[0]}</span>' if delta else ""
    return (f'<div class="kartu {kelas}"{gaya}><div class="atas"><div class="lab">{label}</div>'
            f'<div class="ic">{IKON[ikon]}</div></div>'
            f'<div class="val{kls}">{nilai}</div><div class="ket">{d}{ket}</div></div>')


def grid(kelas, *isi):
    st.markdown(f'<div class="grid {kelas}">{"".join(isi)}</div>', unsafe_allow_html=True)


def intro(teks):
    st.markdown(f'<div class="intro">{teks}</div>', unsafe_allow_html=True)


def kepala(judul, sub, chips=()):
    ch = "".join(f'<span class="chip">{c}</span>' for c in chips)
    st.markdown(f'<div class="kepala"><div><div class="jh">{judul}</div><div class="sh">{sub}</div></div>'
                f'<div>{ch}</div></div>', unsafe_allow_html=True)


def kotak(nama):
    return st.container(key=f"card_{nama}")


def pill(kode, besar=False, tampil="nama"):
    s = EWS[kode]
    teks = {"nama": s["nama"], "sebutan": s["sebutan"]}.get(tampil, f'{s["nama"]} ({s["sebutan"]})')
    return (f'<span class="pill{" besar" if besar else ""}" '
            f'style="background:{s["warna"]};color:{s["teks"]}">{teks}</span>')


def pakai_tema(fig, tinggi=380):
    fig.update_layout(
        template="simple_white", height=tinggi, margin=dict(l=10, r=10, t=20, b=10),
        font=dict(family="Inter, sans-serif", size=13, color=TEKS),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.25, title=None),
    )
    return fig
