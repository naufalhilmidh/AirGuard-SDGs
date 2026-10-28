import streamlit as st

from data import EWS, ringkasan_data, tabel_besok
from ui import kartu

TB, AKHIR, BESOK = tabel_besok()
r = ringkasan_data()


def masuk(tujuan):
    st.session_state["masuk"] = True
    st.session_state["tujuan"] = tujuan
    st.rerun()


def panel_pratinjau():
    jumlah = TB["status"].value_counts().to_dict()
    tiga = "".join(
        f'<div class="tg"><div class="n">{jumlah.get(s["kode"], 0)}</div>'
        f'<div class="l"><span class="t" style="background:{s["warna"]}"></span>{s["sebutan"]}</div></div>'
        for s in EWS)
    atas = TB.sort_values("pm_besok", ascending=False).head(4)
    mx = max(float(atas["pm_besok"].max()), 1.0)
    baris = "".join(
        f'<div class="bar"><span>{x.nama}</span><div class="tr"><i style="width:{x.pm_besok / mx * 100:.0f}%;'
        f'background:{EWS[x.status]["warna"]}"></i></div><b>{x.pm_besok:.0f}</b></div>'
        for x in atas.itertuples())
    return (f'<div class="panel"><div class="ph"><span>Prediksi untuk {BESOK:%d %b %Y}</span>'
            f'<span>{len(TB)} kabupaten/kota</span></div><div class="tiga">{tiga}</div>'
            f'<div class="judulp">Prediksi PM2.5 tertinggi (µg/m³)</div>{baris}</div>')


with st.container(key="hero"):
    kiri, kanan = st.columns([1.15, 1], gap="large", vertical_alignment="center")
    with kiri:
        st.markdown(
            '<div class="eyebrow">SDG 3 · SDG 11 · SDG 13</div>'
            "<h1>Tahu kualitas udara besok, sebelum polusi datang.</h1>"
            f'<p class="lead">Prediksi PM2.5 harian dan peringatan dini kesehatan untuk {r["n_kota"]} kabupaten/kota di '
            f'Pulau Jawa, mencakup sekitar {r["penduduk_juta"]:.0f} juta penduduk.</p>',
            unsafe_allow_html=True)
        b1, _ = st.columns([1.3, 1])
        if b1.button("Masuk ke dashboard", key="btn_ews", use_container_width=True):
            masuk("halaman_ews.py")
    with kanan:
        st.markdown(panel_pratinjau(), unsafe_allow_html=True)

st.markdown(
    '<div class="angkabesar">'
    f'<div><div class="n">{r["n_kota"]}</div><div class="l">kabupaten/kota di {r["n_provinsi"]} provinsi</div></div>'
    f'<div><div class="n">{r["penduduk_juta"]:.0f}<small>juta</small></div><div class="l">penduduk dalam cakupan data</div></div>'
    f'<div><div class="n">{r["n_hari"]}<small>hari</small></div><div class="l">data historis, {r["awal"]:%b %Y} sampai {r["akhir"]:%b %Y}</div></div>'
    f'<div><div class="n">{r["akurasi"] * 100:.1f}<small>%</small></div><div class="l">hari dengan status prediksi sama dengan status sebenarnya</div></div>'
    "</div>", unsafe_allow_html=True)

st.markdown('<div class="bagian">Tiga cara memakai dashboard ini</div>'
            '<div class="sub">Pilih halaman sesuai kebutuhan. Semuanya memakai data yang sama.</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="grid g3">'
    + kartu("EWS harian (H+1)",
            "Untuk masyarakat umum, rumah sakit, dan dinas lingkungan hidup daerah. Status udara besok, peta risiko, "
            "dan rekomendasi singkat tiap daerah.", '<div class="noc">01 · MASYARAKAT</div>', "gelap")
    + kartu("Proyeksi jangka panjang",
            "Untuk Bappeda, perencana tata kota, dan peneliti. Tren musiman, kalender risiko per bulan, dan rekomendasi "
            "kebijakan dari proyeksi.", '<div class="noc">02 · PERENCANA</div>', "putih")
    + kartu("Analitik dan evaluasi",
            "Untuk dosen dan tim peneliti. Akurasi model dibanding tebakan sederhana, galat per provinsi dan bulan, "
            "evaluasi status EWS, serta hubungan PM2.5 dengan cuaca.", '<div class="noc">03 · PENELITI</div>', "putih")
    + "</div>", unsafe_allow_html=True)

st.markdown('<div class="bagian">Cara membaca status</div>'
            '<div class="sub">Tiga status mengikuti rentang PM2.5 harian.</div>', unsafe_allow_html=True)
saran = {0: "Aktivitas di luar ruangan aman dilakukan.",
         1: "Kelompok sensitif sebaiknya mengurangi aktivitas berat di luar ruangan.",
         2: "Disarankan memakai masker dan membatasi aktivitas di luar ruangan."}
st.markdown(
    '<div class="grid g3">' + "".join(
        f'<div class="kartu stat sb" style="--sb:{s["warna"]}"><span class="pill" style="background:{s["warna"]};color:{s["teks"]}">'
        f'{s["nama"]} ({s["sebutan"]})</span><div class="val" style="font-size:1.5rem;margin-top:12px">{s["rentang"]}</div>'
        f'<div class="ket">{saran[s["kode"]]}</div></div>' for s in EWS) + "</div>", unsafe_allow_html=True)

st.markdown('<div class="bagian">Kaitan dengan SDGs</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="grid g3">'
    '<div class="kartu lembut"><div class="sdgno">3<small>Kehidupan sehat dan sejahtera</small></div>'
    '<div class="isi">Target 3.9: mengurangi penyakit dan kematian akibat pencemaran udara. Peringatan dini membantu masyarakat '
    "dan fasilitas kesehatan bersiap sebelum polusi meningkat.</div></div>"
    '<div class="kartu lembut"><div class="sdgno">11<small>Kota dan permukiman berkelanjutan</small></div>'
    '<div class="isi">Target 11.6: mengurangi dampak lingkungan perkotaan, termasuk kualitas udara. Peta risiko dan proyeksi musiman '
    "membantu menentukan wilayah dan waktu yang perlu diprioritaskan.</div></div>"
    '<div class="kartu lembut"><div class="sdgno">13<small>Penanganan perubahan iklim</small></div>'
    '<div class="isi">Pola polusi dibaca bersama dinamika cuaca dan musim, sebagai dasar aksi adaptasi yang mengikuti musim.</div></div>'
    "</div>", unsafe_allow_html=True)

st.markdown(
    '<div class="catatan" style="margin-top:1.4rem">Proyek kelompok mata kuliah SDGs, PENS. Sumber data: Open-Meteo. '
    "Kategori status mengikuti rincian proyek dan bukan klaim medis.</div>", unsafe_allow_html=True)
