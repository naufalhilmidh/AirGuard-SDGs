"""AirGuard SDGs, dashboard 2: sistem peringatan dini (EWS) dan proyeksi jangka panjang.

Jalankan dari akar repo:  python -m streamlit run dashboard_ews/app.py
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="AirGuard SDGs EWS", layout="wide")

from data import muat_proyeksi  # noqa: E402  (harus setelah set_page_config)
from ui import pasang_css  # noqa: E402

pasang_css()
_, _, _, tahun = muat_proyeksi()

if not st.session_state.get("masuk"):
    # tahap 1: hanya landing page, tanpa menu
    st.navigation([st.Page("halaman_beranda.py", title="Beranda")], position="hidden").run()
else:
    st.logo(str(Path(__file__).parent / "logo.svg"), size="large")
    halaman = st.navigation(
        [
            st.Page("halaman_ews.py", title="EWS Harian (H+1)", url_path="ews", default=True),
            st.Page("halaman_proyeksi.py", title=f"Proyeksi {tahun}", url_path="proyeksi"),
            st.Page("halaman_analitik.py", title="Analitik & Evaluasi", url_path="analitik"),
        ],
        position="sidebar",
    )
    with st.sidebar:
        st.markdown('<div class="sb-info"><b>Sumber data</b><br>Open-Meteo, diolah tim AirGuard. '
                    'Status mengikuti rincian proyek dan bukan klaim medis.</div>', unsafe_allow_html=True)
        if st.button("Kembali ke beranda", key="btn_beranda", use_container_width=True):
            st.session_state["masuk"] = False
            st.rerun()
    tujuan = st.session_state.pop("tujuan", None)
    if tujuan and tujuan != "halaman_ews.py":
        st.switch_page(tujuan)
    halaman.run()
