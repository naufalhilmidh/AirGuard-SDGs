import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import EWS, PROVINSI, kode_status, kota_terbesar, tabel_besok
from ui import BIRU, grid, intro, kepala, kotak, pakai_tema, pill, stat

TB, AKHIR, BESOK = tabel_besok()

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


def zoom_peta(t):
    span = max(t["lon"].max() - t["lon"].min(), (t["lat"].max() - t["lat"].min()) * 1.2, 0.3)
    return float(np.clip(8.55 - np.log2(span), 5.0, 10.5))


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
        f'<div class="vl">{r.pm_besok:.0f} <span style="font-size:.8rem;font-weight:500;color:#475569">µg/m³</span></div>'
        f'{pill(r.status, tampil="sebutan")}</div>'
        for r in utama.itertuples()])

    # ---- peta + kartu detail ----
    kiri, kanan = st.columns([1.5, 1], gap="large")
    with kiri:
        with kotak("peta"):
            st.subheader("Peta risiko besok")
            st.caption("Setiap titik adalah satu kabupaten/kota, diwarnai menurut status prediksi besok. "
                       "Lingkaran biru menandai daerah yang dipilih untuk kartu detail.")
            fig = go.Figure()
            sel = t[t["kota"] == kota]
            fig.add_trace(go.Scattermap(lat=sel["lat"], lon=sel["lon"], mode="markers", showlegend=False, hoverinfo="skip",
                                        marker=dict(size=26, color=BIRU, opacity=0.35)))
            for s in EWS:
                x = t[t["status"] == s["kode"]]
                fig.add_trace(go.Scattermap(
                    lat=x["lat"], lon=x["lon"], mode="markers", name=f'{s["nama"]} ({s["sebutan"]})',
                    marker=dict(size=12 if prov == "Semua provinsi" else 15, color=s["warna"]),
                    text=x["nama"], customdata=np.c_[x["pm_besok"], x["provinsi"]],
                    hovertemplate="<b>%{text}</b><br>%{customdata[1]}<br>Prediksi besok: %{customdata[0]:.1f} µg/m³<extra></extra>"))
            fig.update_layout(
                height=460, margin=dict(l=0, r=0, t=0, b=0),
                map=dict(style="carto-positron", center=dict(lat=float(t["lat"].mean()), lon=float(t["lon"].mean())),
                         zoom=zoom_peta(t)),
                legend=dict(orientation="h", y=0.03, yanchor="bottom", x=0.01, bgcolor="rgba(255,255,255,.85)"),
                font=dict(family="Inter, sans-serif", size=12))
            st.plotly_chart(fig)
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
                f'<div class="angka">{row["pm_besok"]:.1f} <small>µg/m³</small></div>'
                f'<div class="kv"><span>PM2.5 hari ini (aktual)</span><b>{row["pm_ini"]:.1f}</b></div>'
                f'<div class="kv"><span>Perubahan</span><b>{"naik" if naik > 0 else "turun"} {abs(naik):.1f}</b></div>'
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
        top = t.sort_values("pm_besok", ascending=False).head(10)
        mx = max(float(top["pm_besok"].max()), 1.0)
        baris = "".join(
            f'<tr><td class="no">{i}</td><td><b>{r.kota}</b></td><td>{r.provinsi}</td><td class="n">{r.pm_ini:.1f}</td>'
            f'<td class="n">{r.pm_besok:.1f}<span class="mini"><i style="width:{r.pm_besok / mx * 100:.0f}%;'
            f'background:{EWS[r.status]["warna"]}"></i></span></td><td>{pill(r.status)}</td></tr>'
            for i, r in enumerate(top.itertuples(), 1))
        st.markdown('<table class="tabelk"><thead><tr><th></th><th>Kabupaten/kota</th><th>Provinsi</th>'
                    '<th class="n">Hari ini</th><th class="n">Prediksi besok</th><th>Status</th></tr></thead>'
                    f"<tbody>{baris}</tbody></table>", unsafe_allow_html=True)


badan()
