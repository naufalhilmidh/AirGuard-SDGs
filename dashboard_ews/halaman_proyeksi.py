import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import (BATAS_BAHAYA, EWS, PROVINSI, TIPE, PENDUDUK, cakupan_provinsi, kode_status, kota_terbesar,
                  muat_data, muat_proyeksi, nama_pendek)
from ui import BIRU, grid, intro, kepala, kotak, pakai_tema, pill, stat

F, METODE, AKHIR, TAHUN = muat_proyeksi()
PRED, PRE, *_ = muat_data()
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember"]
BULAN_PENDEK = [b[:3] for b in BULAN]
# Pola umum musim di Jawa (perkiraan kasar, berbeda tiap wilayah): hujan Nov-Mar, pancaroba Apr-Mei dan Okt, kemarau Jun-Sep.
MUSIM = [(1, 3, "Hujan", "#DBEAFE"), (4, 5, "Pancaroba", "#F1F5F9"), (6, 9, "Kemarau", "#FEF3C7"),
         (10, 10, "Pancaroba", "#F1F5F9"), (11, 12, "Hujan", "#DBEAFE")]

metode_teks = "Pola musiman historis" if METODE == "musiman" else "Prakiraan dari model tim"
kepala(
    f"Proyeksi jangka panjang {AKHIR.year} sampai {TAHUN}",
    "Untuk Bappeda, perencana tata kota, dan peneliti: kapan polusi cenderung tinggi pada tahun depan.",
    [f"{(AKHIR + pd.Timedelta(days=1)):%d %b %Y} sampai 31 Des {TAHUN}", f"Metode: {metode_teks}"],
)


@st.cache_data(show_spinner=False, max_entries=64)
def seri(level, nama):
    kolom = ["pm2_5_prakiraan", "batas_bawah", "batas_atas"]
    if level == "Provinsi":
        proj = F[F["provinsi"] == nama].groupby("tanggal")[kolom].mean().reset_index()
        h = PRED[(PRED["provinsi"] == nama) & PRED["pm2_5_aktual"].notna()]
    else:
        proj = F[F["kota"] == nama][["tanggal", *kolom]]
        h = PRED[(PRED["kota"] == nama) & PRED["pm2_5_aktual"].notna()]
    riwayat = h.groupby("tanggal_prediksi", observed=True)["pm2_5_aktual"].mean().reset_index().tail(120)
    return proj, riwayat


@st.cache_data(show_spinner=False)
def tabel_bulan(dasar):
    x = F[F["tanggal"].dt.year == TAHUN].assign(bulan=lambda d: d["tanggal"].dt.month)
    return x.groupby([dasar, "bulan"])["pm2_5_prakiraan"].mean().unstack().reindex(columns=range(1, 13))


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


def rekomendasi(prov_bulan):
    saran, status = [], pd.DataFrame(kode_status(prov_bulan.to_numpy()), index=prov_bulan.index, columns=prov_bulan.columns)
    bahaya = status.eq(2)
    if bahaya.to_numpy().any():
        rinci = "; ".join(f"{prov} pada {rentang_bulan([m for m in prov_bulan.columns if bahaya.loc[prov, m]])}"
                          for prov in prov_bulan.index if bahaya.loc[prov].any())
        saran.append(f"Pada {TAHUN}, rata-rata PM2.5 bulanan diproyeksikan melewati {BATAS_BAHAYA:.0f} µg/m³ (status Tidak sehat) di: "
                     f"<b>{rinci}</b>. Siapkan razia emisi kendaraan bermotor dan pengendalian pembakaran terbuka sebelum bulan itu, "
                     "serta pertimbangkan WFH parsial dan perluasan Car Free Day pada puncaknya.")
    else:
        rata = prov_bulan.mean()
        puncak = [int(m) for m in rata.sort_values(ascending=False).head(3).index]
        p_top = prov_bulan.stack().idxmax()
        saran.append(f"Tidak ada provinsi yang diproyeksikan melewati {BATAS_BAHAYA:.0f} µg/m³ pada rata-rata bulanan. "
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


@st.fragment
def badan():
    if METODE == "musiman":
        intro(f"<b>Cara membaca:</b> proyeksi ini dihitung dari <i>pola musiman</i> rata-rata data {PRE['tanggal'].min():%b %Y} "
              f"sampai {PRE['tanggal'].max():%b %Y}. Artinya menggambarkan <i>bulan-bulan yang cenderung tinggi</i>, bukan "
              "ramalan harian. Proyeksi ini belum memperhitungkan tren jangka panjang, perubahan kebijakan, atau kejadian "
              "khusus seperti kebakaran lahan. Untuk besok hari, gunakan halaman EWS harian.")
    else:
        intro("<b>Cara membaca:</b> proyeksi berasal dari file prakiraan yang disediakan tim pemodelan. "
              "Semakin jauh tanggalnya, semakin besar ketidakpastiannya.")

    # ---------- tren ----------
    with kotak("tren"):
        st.subheader("Tren PM2.5 jangka panjang")
        c1, c2, _ = st.columns([1, 1.6, 1.4])
        level = c1.radio("Lihat per", ["Provinsi", "Kabupaten/kota"], horizontal=True, key="prj_level")
        if level == "Provinsi":
            nama = c2.selectbox("Provinsi", [p for p in PROVINSI if p in set(F["provinsi"].astype(str))] or PROVINSI, key="prj_prov")
        else:
            opsi = sorted(F["kota"].unique())
            nama = c2.selectbox("Kabupaten/kota", opsi, index=opsi.index(kota_terbesar(opsi)), key="prj_kota",
                                help="Ketik untuk mencari nama.")
        proj, riwayat = seri(level, nama)
        st.caption("Garis abu-abu adalah data aktual 120 hari terakhir. Garis biru adalah proyeksi, dengan pita biru muda "
                   "sebagai rentang harian yang wajar (± satu simpangan baku). Garis merah putus-putus adalah batas bahaya. "
                   "Warna latar menandai pola musim secara umum.")
        if proj.empty:
            st.info("Belum ada data proyeksi untuk pilihan ini.")
            return
        x0 = riwayat["tanggal_prediksi"].min() if not riwayat.empty else proj["tanggal"].min()
        x1 = proj["tanggal"].max()
        fig = go.Figure()
        label_terakhir = None
        for tahun in range(x0.year, x1.year + 1):
            for a, b, label, warna in MUSIM:
                s, e = pd.Timestamp(tahun, a, 1), pd.Timestamp(tahun, b, 1) + pd.offsets.MonthEnd(0)
                s, e = max(s, x0), min(e, x1)
                if s < e:
                    # musim yang bersambung lintas tahun (hujan Nov-Mar) cukup diberi satu label
                    tampil = label if (label != label_terakhir and (e - s).days > 40) else ""
                    fig.add_vrect(x0=s, x1=e, fillcolor=warna, opacity=0.55, line_width=0, layer="below",
                                  annotation_text=tampil, annotation_position="top left",
                                  annotation_font=dict(size=10, color="#475569"))
                    label_terakhir = label
        fig.add_trace(go.Scatter(x=proj["tanggal"], y=proj["batas_atas"], mode="lines", line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=proj["tanggal"], y=proj["batas_bawah"], mode="lines", line=dict(width=0), fill="tonexty",
                                 fillcolor="rgba(30,58,138,0.15)", name="Rentang harian wajar", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=riwayat["tanggal_prediksi"], y=riwayat["pm2_5_aktual"], name="Aktual",
                                 line=dict(color="#64748B", width=1.6)))
        fig.add_trace(go.Scatter(x=proj["tanggal"], y=proj["pm2_5_prakiraan"], name="Proyeksi",
                                 line=dict(color=BIRU, width=2.2)))
        fig.add_hline(y=BATAS_BAHAYA, line=dict(color="#EF4444", width=1.2, dash="dash"),
                      annotation_text=f"Batas bahaya {BATAS_BAHAYA:.0f}", annotation_position="top right",
                      annotation_font=dict(size=11, color="#EF4444"))
        puncak = np.nanmax([proj["batas_atas"].max(), proj["pm2_5_prakiraan"].max(), riwayat["pm2_5_aktual"].max()])
        fig.update_yaxes(title="PM2.5 (µg/m³)", range=[0, max(BATAS_BAHAYA + 10, float(puncak) * 1.1)])
        st.plotly_chart(pakai_tema(fig, 400))

    # ---------- heatmap kalender ----------
    with kotak("kalender"):
        st.subheader(f"Kalender risiko polusi {TAHUN}")
        st.caption(f"Setiap kotak adalah rata-rata proyeksi PM2.5 bulan itu, diwarnai menurut status. "
                   "Dipakai untuk melihat bulan mana yang paling perlu diwaspadai.")
        mode = st.radio("Baris", ["Provinsi", "Kabupaten/kota pilihan"], horizontal=True, key="prj_heat")
        if mode == "Provinsi":
            m = tabel_bulan("provinsi").reindex(PROVINSI).dropna(how="all")
            label = list(m.index)
        else:
            kandidat = sorted(F["kota"].unique())
            awal = sorted([k for k in kandidat if TIPE[k] == "Kota"], key=lambda k: -PENDUDUK[k])[:8]
            pilih = st.multiselect("Kabupaten/kota", kandidat, default=awal, key="prj_heat_kota")
            m = tabel_bulan("kota").reindex(pilih or awal)
            label = [nama_pendek(k) for k in m.index]
        z = kode_status(m.to_numpy())
        warna = [EWS[0]["warna"], EWS[1]["warna"], EWS[2]["warna"]]
        fig2 = go.Figure(go.Heatmap(
            z=z, x=BULAN_PENDEK, y=label, zmin=0, zmax=2, showscale=False, xgap=3, ygap=3,
            colorscale=[[0, warna[0]], [0.25, warna[0]], [0.25, warna[1]], [0.75, warna[1]], [0.75, warna[2]], [1, warna[2]]],
            text=np.round(m.to_numpy()).astype(int).astype(str), texttemplate="%{text}",
            textfont=dict(size=12, color="#0F172A"),
            hovertemplate="%{y}, %{x}: %{text} µg/m³<extra></extra>"))
        fig2.update_yaxes(autorange="reversed")
        fig2.update_xaxes(side="top")
        st.plotly_chart(pakai_tema(fig2, 130 + 44 * len(label)))
        st.markdown(" ".join(pill(s["kode"], tampil="lengkap") for s in EWS)
                    + f' <span class="catatan">&nbsp;Angka di kotak: rata-rata PM2.5 bulanan (µg/m³).</span>',
                    unsafe_allow_html=True)

    # ---------- rekomendasi ----------
    pb = tabel_bulan("provinsi").reindex(PROVINSI).dropna(how="all")
    with kotak("rekomendasi"):
        st.subheader("Rekomendasi kebijakan daerah")
        st.caption("Dihasilkan otomatis dari angka proyeksi di atas, sebagai bahan diskusi. Bukan keputusan kebijakan.")
        st.markdown('<ol class="rek">' + "".join(f"<li>{s}</li>" for s in rekomendasi(pb)) + "</ol>",
                    unsafe_allow_html=True)
        unduh = pb.copy()
        unduh.columns = BULAN
        st.download_button("Unduh proyeksi bulanan per provinsi (CSV)", unduh.round(1).to_csv().encode("utf-8"),
                           file_name=f"airguard_proyeksi_{TAHUN}.csv", mime="text/csv")


badan()
