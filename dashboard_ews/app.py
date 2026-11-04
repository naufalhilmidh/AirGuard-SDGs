"""AirGuard SDGs, dashboard 2: sistem peringatan dini (EWS) dan proyeksi jangka panjang.

Jalankan dari akar repo:  python -m streamlit run dashboard_ews/app.py
"""
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

st.set_page_config(page_title="AirGuard SDGs EWS", layout="wide")

from data import PROVINSI, SEMUA_KOTA, SEMUA_PROV, WILAYAH, muat_data, muat_proyeksi  # noqa: E402  (harus setelah set_page_config)
from ui import pasang_css  # noqa: E402

pasang_css()
_, _, _, tahun = muat_proyeksi()

if not st.session_state.get("masuk"):
    # tahap 1: hanya landing page, tanpa menu
    st.navigation([st.Page("halaman_beranda.py", title="Beranda")], position="hidden").run()
else:
    # klik logo = kembali ke beranda (membuka ulang alamat utama aplikasi)
    alamat = urlparse(st.context.url or "")
    st.logo(str(Path(__file__).parent / "logo.svg"), size="large",
            link=f"{alamat.scheme}://{alamat.netloc}/" if alamat.netloc else None)
    halaman = st.navigation(
        [
            st.Page("halaman_ews.py", title="EWS Harian (H+1)", url_path="ews", default=True),
            st.Page("halaman_proyeksi.py", title=f"Proyeksi {tahun}", url_path="proyeksi"),
            st.Page("halaman_analitik.py", title="Analitik & Evaluasi", url_path="analitik"),
        ],
        position="sidebar",
    )
    with st.sidebar:
        # Pilihan wilayah dipasang sekali di sini, lalu dibaca oleh semua halaman lewat wilayah_dipilih().
        st.markdown("**Wilayah**")
        prov_pilih = st.selectbox("Provinsi", [SEMUA_PROV, *PROVINSI], key="g_prov")
        daftar_kota = sorted(WILAYAH["kota"] if prov_pilih == SEMUA_PROV else WILAYAH.loc[WILAYAH["provinsi"] == prov_pilih, "kota"])
        kota_pilih = st.selectbox("Kabupaten/kota", [SEMUA_KOTA, *daftar_kota], key=f"g_kota_{prov_pilih}",
                                  help="Ketik untuk mencari nama.")
        st.session_state["wil_prov"], st.session_state["wil_kota"] = prov_pilih, kota_pilih
        sumber = muat_data()[4]
        catatan = {"baseline": "<br><br><b>Catatan:</b> prediksi besok sementara memakai baseline persistence "
                               "(besok sama dengan hari ini) karena keluaran model tim belum tersedia.",
                   "contoh": "<br><br><b>Catatan:</b> seluruh angka adalah data contoh (sintetis).", "tim": ""}[sumber]
        st.markdown('<div class="sb-info"><b>Sumber data</b><br>Open-Meteo, diolah tim AirGuard. '
                    'Status mengikuti rincian proyek dan bukan klaim medis.' + catatan + '</div>', unsafe_allow_html=True)
    tujuan = st.session_state.pop("tujuan", None)
    if tujuan and tujuan != "halaman_ews.py":
        st.switch_page(tujuan)
    halaman.run()