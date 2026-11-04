import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import peta
from data import EWS, PROVINSI, kode_status, kota_terbesar, muat_klaster, tabel_besok
from ui import BIRU, grid, intro, kepala, kotak, pakai_tema, pill, stat

TB, AKHIR, BESOK = tabel_besok()
WARNA_KLASTER = {"rendah-stabil": "#10B981", "sedang-musiman": "#F59E0B", "tinggi-persisten": "#EF4444"}

REKOMENDASI = {
    0: ["Aktivitas di luar ruangan aman dilakukan.",
        "Tidak diperlukan perlindungan khusus."],
    1: ["Kelompok sensitif (anak, lansia, penderita asma) sebaiknya mengurangi aktivitas berat di luar ruangan.",
        "Pantau kondisi udara pada hari berikutnya."],
    2: ["Disarankan memakai masker (N95 atau KN95) bila harus beraktivitas di luar ruangan.",
        "Siswa TK dan SD sebaiknya membatasi olahraga di luar ruangan.",
        "Penderita asma disarankan memakai penyaring udara di dalam ruangan dan menyiapkan obat rutinnya."],
}


def ventilasi(kmh):
    """Ambang indikatif: kurang dari 7 km/jam (sekitar 2 m/s) dianggap lemah, di atas 14 km/jam baik."""
    if np.isnan(kmh):
        return "tidak ada data"
    return "lemah" if kmh < 7.2 else ("sedang" if kmh < 14.4 else "baik")


def tampil_prediksi(nilai, status):
    if pd.isna(nilai):
        return f"{EWS[int(status)]['nama']} ({EWS[int(status)]['sebutan']})"
    return f"{nilai:.1f} µg/m³"


kepala(
    "EWS harian (H+1)",
    "Status kualitas udara besok untuk masyarakat umum, rumah sakit, dan dinas lingkungan hidup daerah.",
    [f"Data aktual sampai {AKHIR:%d %b %Y}", f"Prediksi untuk {BESOK:%d %b %Y}"],
)


@st.fragment
def badan():
    f1, f2, f3 = st.columns([1, 1.4, 1.2], vertical_alignment="bottom")
    prov = f1.selectbox("Provinsi", ["Semua provinsi", *PROVINSI], key="ews_prov")
    t = TB if prov == "Semua provinsi" else TB[TB["provinsi"] == prov]
    opsi = sorted(t["kota"])
    kota = f2.selectbox("Kabupaten/kota untuk kartu detail", opsi, index=opsi.index(kota_terbesar(opsi)),
                        key=f"ews_kota_{prov}", help="Ketik untuk mencari nama.")
    unduh = t[["kota", "provinsi", "pm_ini", "pm_besok", "status"]].rename(columns={
        "kota": "kabupaten_kota", "pm_ini": "pm2_5_hari_ini", "pm_besok": "pm2_5_prediksi_besok", "status": "kode_status"})
    unduh["status"] = unduh["kode_status"].map(lambda k: EWS[k]["nama"])
    f3.download_button("Unduh status besok (CSV)", unduh.to_csv(index=False).encode("utf-8"),
                       file_name=f"airguard_status_{BESOK:%Y%m%d}.csv", mime="text/csv", use_container_width=True)

    intro("<b>Halaman ini menjawab:</b> bagaimana kualitas udara besok, dan daerah mana yang perlu diwaspadai? "
          "Angka besok adalah <i>prediksi model</i>, sedangkan angka hari ini adalah data aktual terakhir.")

    # ---- ringkasan status ----
    jumlah = t["status"].value_counts().to_dict()
    kemarin = pd.Series(kode_status(t["pm_ini"].to_numpy())).value_counts().to_dict()

    def delta(kode):
        d = jumlah.get(kode, 0) - kemarin.get(kode, 0)
        if d == 0:
            return ("sama seperti hari ini", "netral")
        baik = (d > 0) if kode == 0 else (d < 0 if kode == 2 else None)
        return (f"{d:+d} dari hari ini", "netral" if baik is None else ("baik" if baik else "buruk"))

    grid("g4",
         stat("Wilayah dipantau", f"{len(t)}", "kabupaten/kota" + ("" if prov == "Semua provinsi" else f" di {prov}"), "pin", gelap=True),
         *[stat(f'{s["nama"]} ({s["sebutan"]})', f'{jumlah.get(s["kode"], 0)}', f'PM2.5 {s["rentang"]}',
                "pin" if s["kode"] == 0 else ("awas" if s["kode"] == 2 else "tren"), s["warna"], delta=delta(s["kode"]))
           for s in EWS])

    # ---- kota utama ----
    utama = t.sort_values("penduduk", ascending=False)
    utama = utama[utama["tipe"] == "Kota"].head(6) if (utama["tipe"] == "Kota").any() else utama.head(6)
    st.subheader("Status kota-kota besar besok")
    grid("g6", *[
        f'<div class="kartu kota-strip" style="--sb:{EWS[r.status]["warna"]}"><div class="nm">{r.nama}</div>'
        f'<div class="vl">{tampil_prediksi(r.pm_besok, r.status)}</div>'
        f'{pill(r.status, tampil="sebutan")}</div>'
        for r in utama.itertuples()])

    # ---- peta + kartu detail ----
    sel = t[t["kota"] == kota]
    kiri, kanan = st.columns([1.5, 1], gap="large")
    with kiri:
        with kotak("peta"):
            klaster = muat_klaster()
            mode = "Status besok"
            if peta.tersedia() and klaster is not None:
                mode = st.segmented_control("Tampilan peta", ["Status besok", "Zona klaster"], default="Status besok",
                                            key="mode_peta", label_visibility="collapsed") or "Status besok"
            if not peta.tersedia():
                st.subheader("Peta risiko besok")
                st.info("Berkas batas wilayah referensi/batas_kabkota_jawa.geojson belum ada.")
            else:
                warna, tips = {}, {}
                if mode == "Zona klaster":
                    st.subheader("Peta zona klaster")
                    st.caption("Zona jangka panjang hasil K-Means tim, jadi tidak berubah dari hari ke hari. "
                               "Warna ini pembeda karakter wilayah, bukan tingkat bahaya harian.")
                    zona = klaster.set_index("kota")
                    for r in t.itertuples():
                        if r.kota in zona.index:
                            z = zona.loc[r.kota]
                            warna[r.kode_kabkota] = WARNA_KLASTER[z["nama_cluster"]]
                            tips[r.kode_kabkota] = (f"<b>{r.kota}</b><br>Zona {z['nama_cluster']}<br>Rata-rata PM2.5 jangka panjang "
                                                    f"{z['rata_rata_pm25']:.1f} µg/m³<br>Hari tinggi {z['persentase_hari_tinggi']:.1f}%")
                    legenda = "".join(f'<span class="pill" style="background:{w};color:#fff">{n}</span>' for n, w in WARNA_KLASTER.items())
                else:
                    st.subheader("Peta risiko besok")
                    st.caption("Setiap wilayah diwarnai menurut status prediksi besok. Arahkan kursor untuk melihat angkanya, "
                               "tarik untuk menggeser, gulir ganda untuk kembali. Garis biru tebal menandai daerah pada kartu detail.")
                    for r in t.itertuples():
                        st_ = EWS[r.status]
                        warna[r.kode_kabkota] = st_["warna"]
                        tips[r.kode_kabkota] = (f"<b>{r.kota}</b><br>{r.provinsi}<br>Prediksi besok {tampil_prediksi(r.pm_besok, r.status)} "
                                                f"(hari ini {r.pm_ini:.1f})<br>Status {st_['nama']} ({st_['sebutan']})")
                    legenda = "".join(f'<span class="pill" style="background:{x["warna"]};color:{x["teks"]}">{x["nama"]} ({x["sebutan"]})</span>' for x in EWS)
                st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:2px 0 8px">{legenda}</div>', unsafe_allow_html=True)
                st.plotly_chart(peta.gambar(warna, tips, pilih=sel.iloc[0]["kode_kabkota"],
                                            batas=None if prov == "Semua provinsi" else set(t["kode_kabkota"]),
                                            kunci=f"peta-{prov}"), config=peta.KONFIG_PETA, key="peta_ews")
    with kanan:
        row = sel.iloc[0]
        s = EWS[int(row["status"])]
        naik = row["perubahan"]
        kmh = row["angin_kmh"]
        angin = "tidak ada data" if np.isnan(kmh) else f"{kmh:.1f} km/jam ({kmh / 3.6:.1f} m/s)"
        with kotak("detail"):
            st.markdown(
                f'<div class="jud" style="font-size:1.05rem">{row["kota"]}</div>'
                f'<div class="catatan">{row["provinsi"]} · prediksi untuk {BESOK:%d %b %Y}</div>'
                f'<div style="margin:12px 0 4px">{pill(int(row["status"]), besar=True, tampil="lengkap")}</div>'
                f'<div class="angka">{tampil_prediksi(row["pm_besok"], row["status"])}</div>'
                f'<div class="kv"><span>PM2.5 hari ini (aktual)</span><b>{row["pm_ini"]:.1f}</b></div>'
                f'<div class="kv"><span>Perubahan</span><b>{"tidak tersedia untuk model kategori" if pd.isna(naik) else ("tetap" if abs(naik) < 0.05 else ("naik " if naik > 0 else "turun ") + f"{abs(naik):.1f}")}</b></div>'
                f'<div class="kv"><span>Kecepatan angin hari ini</span><b>{angin}</b></div>'
                f'<div class="kv"><span>Ventilasi udara</span><b>{ventilasi(kmh)}</b></div>'
                f'<div class="jud" style="margin-top:16px">Rekomendasi</div>'
                f'<ul class="rek">{"".join(f"<li>{x}</li>" for x in REKOMENDASI[int(row["status"])])}</ul>'
                f'<div class="catatan" style="margin-top:10px">Ringkasan umum berdasarkan status PM2.5, bukan saran medis. '
                f'Batas ventilasi bersifat indikatif.</div>',
                unsafe_allow_html=True)

    # ---- peringkat ----
    with kotak("peringkat"):
        st.subheader("Prediksi tertinggi besok")
        st.caption("Sepuluh kabupaten/kota dengan prediksi PM2.5 tertinggi pada filter yang dipilih. "
                   "Faktor yang diandalkan model dibahas di halaman Analitik & Evaluasi.")
        mode_kategori = t["pm_besok"].isna().all()
        top = (t.sort_values("status", ascending=False).head(10)
               if mode_kategori else t.sort_values("pm_besok", ascending=False).head(10))
        mx = max(float(top["pm_besok"].max()), 1.0) if not mode_kategori else 1.0
        baris = "".join(
            f'<tr><td class="no">{i}</td><td><b>{r.kota}</b></td><td>{r.provinsi}</td><td class="n">{r.pm_ini:.1f}</td>'
            f'<td class="n">{tampil_prediksi(r.pm_besok, r.status)}<span class="mini"><i style="width:{70 if mode_kategori else r.pm_besok / mx * 100:.0f}%;'
            f'background:{EWS[r.status]["warna"]}"></i></span></td><td>{pill(r.status)}</td></tr>'
            for i, r in enumerate(top.itertuples(), 1))
        st.markdown('<table class="tabelk"><thead><tr><th></th><th>Kabupaten/kota</th><th>Provinsi</th>'
                    '<th class="n">Hari ini</th><th class="n">Prediksi besok</th><th>Status</th></tr></thead>'
                    f"<tbody>{baris}</tbody></table>", unsafe_allow_html=True)


badan()
