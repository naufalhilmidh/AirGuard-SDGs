import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import (BATAS_BAHAYA, CUACA, EWS, PENDUDUK, PROVINSI, WARNA_PROVINSI, kota_terbesar, muat_data)
from ui import BIRU, grid, intro, kepala, kotak, pakai_tema, stat

PRED, PRE, METRIK, FITUR, CONTOH, _ = muat_data()
SEMUA = "Semua provinsi"
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember"]
LABEL_FITUR = {
    "pm2_5_lag_1": "PM2.5 kemarin", "pm2_5_lag_7": "PM2.5 tujuh hari lalu", "pm2_5": "PM2.5 hari ini",
    "pm2_5_rolling_3": "Rata-rata PM2.5 3 hari", "pm2_5_rolling_7": "Rata-rata PM2.5 7 hari",
    "bulan": "Bulan (pola musiman)", "wind_speed_10m": "Kecepatan angin",
    "relative_humidity_2m": "Kelembapan", "precipitation": "Curah hujan", "temperature_2m": "Suhu",
    "surface_pressure": "Tekanan udara", "cloud_cover": "Tutupan awan",
}


# ====================== perhitungan (di-cache) ======================
@st.cache_data(show_spinner=False, max_entries=16)
def evaluasi(prov):
    """Metrik regresi, pembanding persistence, galat per bulan, dan matriks konfusi status EWS."""
    d = PRED[PRED["pm2_5_aktual"].notna()]
    if prov != SEMUA:
        d = d[d["provinsi"] == prov]
    d = d.sort_values(["kota", "tanggal_prediksi"])
    a, p = d["pm2_5_aktual"].to_numpy(float), d["pm2_5_prediksi"].to_numpy(float)
    e = p - a
    mae, rmse, bias = float(np.abs(e).mean()), float(np.sqrt((e ** 2).mean())), float(e.mean())
    r2 = float(1 - (e ** 2).sum() / ((a - a.mean()) ** 2).sum())

    # pembanding persistence: "besok sama dengan hari ini" (hanya pasangan hari yang berurutan dalam satu kota)
    kode = pd.factorize(d["kota"])[0]
    tgl = d["tanggal_prediksi"].to_numpy()
    sah = np.r_[False, (kode[1:] == kode[:-1]) & ((tgl[1:] - tgl[:-1]) == np.timedelta64(1, "D"))]
    pers = np.r_[np.nan, a[:-1]]
    if sah.any():
        mae_pers = float(np.abs(a - pers)[sah].mean())
        mae_model_sah = float(np.abs(e)[sah].mean())
        skill = 1 - mae_model_sah / mae_pers if mae_pers > 0 else np.nan
    else:
        mae_pers, skill = np.nan, np.nan

    bulan = pd.Series(np.abs(e), index=d.index).groupby(d["tanggal_prediksi"].dt.month).mean()

    cm = np.zeros((3, 3), dtype=int)
    np.add.at(cm, (d["st_aktual"].to_numpy(int), d["st_prediksi"].to_numpy(int)), 1)

    rng = np.random.default_rng(0)
    sampel_e = e[rng.choice(len(e), min(len(e), 20000), replace=False)]
    return dict(n=len(d), mae=mae, rmse=rmse, r2=r2, bias=bias, mae_pers=mae_pers, skill=skill,
                bulan=bulan, cm=cm, sampel_e=sampel_e)


@st.cache_resource
def galat_provinsi():
    d = PRED[PRED["pm2_5_aktual"].notna()]
    e = d["pm2_5_prediksi"] - d["pm2_5_aktual"]
    t = pd.DataFrame({"provinsi": d["provinsi"].astype(str).to_numpy(), "ae": np.abs(e.to_numpy()), "e": e.to_numpy()})
    g = t.groupby("provinsi").agg(MAE=("ae", "mean"), Bias=("e", "mean"), n=("ae", "size")).reset_index()
    return g.set_index("provinsi").reindex([p for p in PROVINSI if p in set(g["provinsi"])]).reset_index()


@st.cache_data(show_spinner=False, max_entries=16)
def contoh_scatter(prov):
    d = PRED[PRED["pm2_5_aktual"].notna()]
    if prov != SEMUA:
        d = d[d["provinsi"] == prov]
    s = d.sample(min(len(d), 1500), random_state=0)[["provinsi", "pm2_5_aktual", "pm2_5_prediksi"]].copy()
    s["provinsi"] = s["provinsi"].astype(str)
    return s


@st.cache_data(show_spinner=False, max_entries=16)
def hitung_cuaca(prov, grup):
    d = PRE if prov == SEMUA else PRE[PRE["provinsi"] == prov]
    if grup == "kota":  # satu provinsi dipilih: tampilkan 15 kabupaten/kota berpenduduk terbanyak
        besar = sorted(d["kota"].astype(str).unique(), key=lambda k: -PENDUDUK[k])[:15]
        d = d[d["kota"].isin(besar)]
    harian = d.groupby([grup, "tanggal"], as_index=False, observed=True)[["pm2_5", *CUACA]].mean()
    korelasi = pd.DataFrame({k: g[list(CUACA)].corrwith(g["pm2_5"]) for k, g in harian.groupby(grup, observed=True)}
                            ).T.rename(columns=CUACA)
    korelasi.index = korelasi.index.astype(str)
    bulanan = d.assign(bulan=d["tanggal"].dt.month).groupby(["bulan", grup], as_index=False, observed=True)["pm2_5"].mean()
    bulanan[grup] = bulanan[grup].astype(str)
    contoh = d.sample(min(len(d), 1500), random_state=0)[["kota", "provinsi", "pm2_5", *CUACA]].copy()
    contoh["kota"], contoh["provinsi"] = contoh["kota"].astype(str), contoh["provinsi"].astype(str)
    return korelasi, bulanan, contoh


@st.cache_data(show_spinner=False, max_entries=16)
def korelasi_gabungan(prov):
    d = PRE if prov == SEMUA else PRE[PRE["provinsi"] == prov]
    return d[list(CUACA)].corrwith(d["pm2_5"])


def temuan(ev, prov):
    t = []
    if abs(ev["bias"]) < 0.05 * ev["mae"]:
        bias_teks = "Hampir tanpa bias: kelebihan dan kekurangan prediksi saling mengimbangi."
    else:
        bias_teks = f"Bias {ev['bias']:+.1f}: rata-rata prediksi cenderung {'terlalu tinggi' if ev['bias'] > 0 else 'terlalu rendah'}."
    t.append(f"Prediksi rata-rata meleset <b>{ev['mae']:.1f} µg/m³</b> (RMSE {ev['rmse']:.1f}, R² {ev['r2']:.2f}). {bias_teks}")
    if not np.isnan(ev["skill"]):
        if ev["skill"] > 0:
            t.append(f"Dibanding tebakan sederhana <i>persistence</i> (besok = hari ini, MAE {ev['mae_pers']:.1f}), "
                     f"galat model <b>{ev['skill'] * 100:.0f}% lebih rendah</b>.")
        else:
            t.append(f"Model <b>belum mengalahkan</b> tebakan sederhana persistence (besok = hari ini, MAE {ev['mae_pers']:.1f}); "
                     f"galatnya {abs(ev['skill']) * 100:.0f}% lebih tinggi.")
    if prov == SEMUA:
        g = galat_provinsi()
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
        t.append(f"Dari <b>{int(cm[2].sum())}</b> hari berstatus Tidak sehat, model berhasil memperingatkan <b>{rec:.0f}%</b> "
                 f"(precision {prec:.0f}%).")
    else:
        t.append("Tidak ada hari berstatus Tidak sehat pada data evaluasi, sehingga kemampuan peringatan dini untuk status "
                 "tertinggi belum bisa diuji.")
    kor = korelasi_gabungan(prov).dropna()
    if len(kor):
        k = kor.abs().idxmax()
        t.append(f"Variabel cuaca dengan hubungan terkuat terhadap PM2.5: <b>{CUACA[k]}</b> (r = {kor[k]:+.2f}). "
                 "Ini pola yang berkaitan, bukan bukti sebab-akibat.")
    return t


def episode(d, ambang):
    f = d[d["pm2_5_aktual"] > ambang].sort_values("tanggal_prediksi")
    if f.empty:
        return pd.DataFrame()
    grup = f["tanggal_prediksi"].diff().dt.days.ne(1).cumsum()
    e = f.groupby(grup).agg(Mulai=("tanggal_prediksi", "min"), Selesai=("tanggal_prediksi", "max"),
                            Puncak=("pm2_5_aktual", "max")).reset_index(drop=True)
    e["Durasi (hari)"] = (e["Selesai"] - e["Mulai"]).dt.days + 1
    e["Mulai"], e["Selesai"] = e["Mulai"].dt.strftime("%d %b %Y"), e["Selesai"].dt.strftime("%d %b %Y")
    return e.sort_values("Puncak", ascending=False)


# ====================== tab 1: evaluasi model ======================
@st.fragment
def tab_evaluasi(prov):
    ev = evaluasi(prov)
    with st.expander("Arti istilah di halaman ini"):
        st.markdown(
            "- **MAE**: rata-rata selisih absolut prediksi dan kenyataan (µg/m³). Metrik utama, makin kecil makin baik.\n"
            "- **RMSE**: seperti MAE tetapi lebih menghukum kesalahan besar.\n"
            "- **R²**: porsi variasi PM2.5 yang dijelaskan model (maksimum 1).\n"
            "- **Bias**: rata-rata (prediksi − aktual). Positif berarti cenderung terlalu tinggi.\n"
            "- **Persistence**: tebakan sederhana bahwa PM2.5 besok sama dengan hari ini. Model hanya berguna kalau "
            "konsisten lebih baik dari ini.\n"
            "- **Recall status**: dari semua hari yang sebenarnya berstatus tertentu, berapa persen yang terdeteksi model. "
            "Untuk peringatan dini, recall status Tidak sehat paling penting.\n"
            "- **Precision status**: dari semua hari yang diprediksi berstatus tertentu, berapa persen yang benar."
        )
    grid(
        "g4",
        stat("MAE", f"{ev['mae']:.2f}", f"µg/m³ · persistence: {ev['mae_pers']:.2f}" if not np.isnan(ev["mae_pers"]) else "µg/m³", "target"),
        stat("RMSE", f"{ev['rmse']:.2f}", "µg/m³", "grafik"),
        stat("R²", f"{ev['r2']:.3f}", "makin dekat 1 makin baik", "tren"),
        stat("Bias", f"{ev['bias']:+.2f}", "µg/m³ · positif = terlalu tinggi", "awas"),
    )
    st.caption(f"Dihitung dari {ev['n']:,} pasangan prediksi dan nilai aktual di file prediksi".replace(",", "."))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("sebar"):
            st.subheader("Aktual vs prediksi")
            st.caption("Satu titik adalah satu hari di satu kabupaten/kota (sampel 1.500 titik). Makin dekat ke garis putus-putus, "
                       "makin tepat. Sebaran yang melebar di nilai tinggi berarti model kesulitan pada polusi tinggi.")
            s = contoh_scatter(prov)
            fig = px.scatter(s, x="pm2_5_aktual", y="pm2_5_prediksi", color="provinsi", opacity=0.5,
                             color_discrete_map=WARNA_PROVINSI,
                             labels={"pm2_5_aktual": "Aktual (µg/m³)", "pm2_5_prediksi": "Prediksi (µg/m³)", "provinsi": "Provinsi"})
            mx = float(max(s["pm2_5_aktual"].max(), s["pm2_5_prediksi"].max()))
            fig.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines", name="Prediksi = aktual",
                                     line=dict(color="#64748B", dash="dot")))
            st.plotly_chart(pakai_tema(fig, 360))
    with kanan:
        with kotak("galat"):
            st.subheader("Sebaran galat")
            st.caption("Histogram selisih prediksi dikurangi aktual. Puncak yang berada di nol dan simetris menandakan model "
                       "tidak condong ke satu arah. Ekor panjang di kanan berarti sesekali meleset jauh ke atas.")
            fig2 = go.Figure(go.Histogram(x=ev["sampel_e"], nbinsx=50, marker_color=BIRU, opacity=0.85))
            fig2.add_vline(x=0, line=dict(color="#EF4444", dash="dash", width=1.2))
            fig2.update_xaxes(title="Prediksi − aktual (µg/m³)")
            fig2.update_yaxes(title="Jumlah hari")
            st.plotly_chart(pakai_tema(fig2, 360))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("galat_prov"):
            st.subheader("Galat per provinsi")
            st.caption("MAE tiap provinsi (seluruh data). Provinsi dengan batang tinggi adalah yang paling sulit diprediksi.")
            g = galat_provinsi()
            fig3 = px.bar(g, x="provinsi", y="MAE", color="provinsi", color_discrete_map=WARNA_PROVINSI, text_auto=".1f")
            fig3.update_layout(showlegend=False)
            fig3.update_xaxes(title=None)
            fig3.update_yaxes(title="MAE (µg/m³)")
            st.plotly_chart(pakai_tema(fig3, 320))
    with kanan:
        with kotak("galat_bulan"):
            st.subheader("Galat per bulan")
            st.caption("MAE menurut bulan kalender. Galat yang naik di musim kemarau biasanya menandakan polusi tinggi "
                       "memang lebih sulit diprediksi.")
            b = ev["bulan"].reset_index()
            b.columns = ["bulan", "MAE"]
            b["nama"] = b["bulan"].map(lambda m: BULAN[int(m) - 1][:3])
            fig4 = px.bar(b, x="nama", y="MAE", color_discrete_sequence=[BIRU], text_auto=".1f")
            fig4.update_xaxes(title=None)
            fig4.update_yaxes(title="MAE (µg/m³)")
            st.plotly_chart(pakai_tema(fig4, 320))

    # ---------- evaluasi status EWS ----------
    with kotak("ews_eval"):
        st.subheader("Evaluasi status peringatan dini (EWS)")
        st.caption("Membandingkan status sebenarnya (baris) dengan status prediksi (kolom). Diagonal adalah prediksi yang benar. "
                   "Persentase dihitung per baris, jadi angka diagonal adalah recall. Sel di bawah diagonal pada baris Tidak sehat "
                   "adalah peringatan yang terlewat.")
        cm = ev["cm"]
        total = cm.sum(axis=1, keepdims=True)
        pct = np.divide(cm, total, out=np.zeros(cm.shape), where=total > 0) * 100
        nama = [s["nama"] for s in EWS]
        teks = [[f"{cm[i, j]}<br>{pct[i, j]:.0f}%" for j in range(3)] for i in range(3)]
        k1, k2 = st.columns([1.2, 1], gap="large")
        with k1:
            fig5 = go.Figure(go.Heatmap(
                z=pct, x=nama, y=nama, zmin=0, zmax=100, showscale=False, xgap=3, ygap=3,
                colorscale=[[0, "#F1F5F9"], [1, "#93B4F0"]], text=teks, texttemplate="%{text}",
                textfont=dict(size=13, color="#0F172A"),
                hovertemplate="Sebenarnya %{y}, diprediksi %{x}<extra></extra>"))
            fig5.update_yaxes(autorange="reversed", title="Status sebenarnya")
            fig5.update_xaxes(side="top", title="Status prediksi")
            st.plotly_chart(pakai_tema(fig5, 330))
        with k2:
            prec = np.divide(np.diag(cm), cm.sum(axis=0), out=np.full(3, np.nan), where=cm.sum(axis=0) > 0) * 100
            rec = np.divide(np.diag(cm), cm.sum(axis=1), out=np.full(3, np.nan), where=cm.sum(axis=1) > 0) * 100
            f1 = 2 * prec * rec / (prec + rec)
            tabel = pd.DataFrame({"Status": [f'{s["nama"]} ({s["sebutan"]})' for s in EWS], "Jumlah hari": cm.sum(axis=1),
                                  "Recall": rec, "Precision": prec, "F1": f1})
            st.dataframe(tabel, hide_index=True, column_config={
                "Recall": st.column_config.NumberColumn(format="%.1f%%"),
                "Precision": st.column_config.NumberColumn(format="%.1f%%"),
                "F1": st.column_config.NumberColumn(format="%.1f%%")})
            akurasi = np.trace(cm) / cm.sum() * 100
            st.markdown(f'<div class="catatan">Akurasi status keseluruhan {akurasi:.1f}%. Status yang jarang terjadi '
                        "mudah terlihat bagus pada akurasi, jadi baca recall dan precision tiap status. "
                        "Tanda – berarti status itu tidak pernah muncul.</div>", unsafe_allow_html=True)

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("metrik_tim"):
            st.subheader("Perbandingan model (hasil evaluasi tim)")
            st.caption("Dari file model_metrics.csv. Sel biru muda adalah nilai terbaik di kolomnya.")
            st.dataframe(
                METRIK.style.format({"MAE": "{:.2f}", "RMSE": "{:.2f}", "R2": "{:.2f}"})
                .highlight_min(subset=["MAE", "RMSE"], color="#DBEAFE").highlight_max(subset=["R2"], color="#DBEAFE"),
                hide_index=True, height=35 * (len(METRIK) + 1) + 3)
            m = METRIK.sort_values("MAE", ascending=False)
            fig6 = px.bar(m, x="MAE", y="model", orientation="h", color_discrete_sequence=[BIRU])
            fig6.update_yaxes(title=None)
            st.plotly_chart(pakai_tema(fig6, 240))
    with kanan:
        with kotak("fitur"):
            st.subheader("Fitur yang paling dipakai model")
            st.caption("Feature importance global. Fitur berawalan PM2.5 adalah riwayat PM2.5. Ini menunjukkan apa yang diandalkan "
                       "model, bukan penyebab polusi.")
            f = FITUR.sort_values("importance").tail(10).copy()
            f["label"] = f["feature"].map(lambda x: LABEL_FITUR.get(x, x))
            fig7 = px.bar(f, x="importance", y="label", orientation="h", color_discrete_sequence=[BIRU])
            fig7.update_yaxes(title=None)
            fig7.update_xaxes(title="Feature importance")
            st.plotly_chart(pakai_tema(fig7, 420))


# ====================== tab 2: tren dan episode ======================
@st.fragment
def tab_tren(prov):
    ada = PRED["kota"].astype(str).unique() if prov == SEMUA else PRED.loc[PRED["provinsi"] == prov, "kota"].astype(str).unique()
    daftar = sorted(ada)
    f0, f1, f2, _ = st.columns([1.7, 1.5, 1.1, 0.4], gap="large")
    level = f0.radio("Lihat", ["Kabupaten/kota", "Provinsi"], horizontal=True, key="an_level")
    if level == "Provinsi":
        opsi = [p for p in PROVINSI if prov in (SEMUA, p)]
        nama = f1.selectbox("Provinsi", opsi, key="an_prov_tren")
        d = (PRED[(PRED["provinsi"] == nama)].groupby("tanggal_prediksi", as_index=False)[["pm2_5_aktual", "pm2_5_prediksi"]].mean())
        d["error"] = d["pm2_5_prediksi"] - d["pm2_5_aktual"]
    else:
        nama = f1.selectbox("Kabupaten/kota", daftar, index=daftar.index(kota_terbesar(daftar)), key=f"an_kota_{prov}",
                            help="Ketik untuk mencari nama.")
        d = PRED[PRED["kota"] == nama]
    ambang = f2.number_input("Ambang polusi tinggi (µg/m³)", value=float(BATAS_BAHAYA), step=1.0, format="%.1f", key="an_ambang",
                             help="Bawaan: batas status Tidak sehat.")
    d = d.sort_values("tanggal_prediksi").copy()
    d["Rata-rata 7 hari"] = d["pm2_5_aktual"].rolling(7, min_periods=1).mean()

    with kotak("tren"):
        st.subheader(f"PM2.5 aktual dan prediksi, {nama}")
        st.caption("Garis biru tua adalah nilai sebenarnya, oranye putus-putus adalah prediksi, abu-abu adalah rata-rata 7 hari. "
                   "Garis merah putus-putus adalah ambang polusi tinggi.")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d["tanggal_prediksi"], y=d["pm2_5_aktual"], name="Aktual", line=dict(color=BIRU, width=2)))
        fig.add_trace(go.Scatter(x=d["tanggal_prediksi"], y=d["pm2_5_prediksi"], name="Prediksi",
                                 line=dict(color="#F97316", width=1.6, dash="dash")))
        fig.add_trace(go.Scatter(x=d["tanggal_prediksi"], y=d["Rata-rata 7 hari"], name="Rata-rata 7 hari",
                                 line=dict(color="#94A3B8", width=1.4, dash="dot")))
        fig.add_hline(y=ambang, line=dict(color="#EF4444", width=1, dash="longdash"),
                      annotation_text=f"Ambang {ambang:.1f}", annotation_position="top left",
                      annotation_font=dict(size=11, color="#EF4444"))
        fig.update_yaxes(title="PM2.5 (µg/m³)")
        st.plotly_chart(pakai_tema(fig, 380))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("selisih"):
            st.subheader("Selisih prediksi dan aktual")
            st.caption("Di atas nol berarti model terlalu tinggi, di bawah nol terlalu rendah.")
            e = d.dropna(subset=["pm2_5_aktual"])
            fig2 = go.Figure(go.Scatter(x=e["tanggal_prediksi"], y=e["error"], mode="lines", fill="tozeroy",
                                        line=dict(color=BIRU, width=1), fillcolor="rgba(30,58,138,0.22)"))
            fig2.update_yaxes(title="Prediksi − aktual (µg/m³)", zeroline=True, zerolinecolor="#94A3B8")
            st.plotly_chart(pakai_tema(fig2, 300))
    with kanan:
        with kotak("episode"):
            st.subheader("Episode polusi tinggi")
            st.caption("Periode hari berturut-turut ketika PM2.5 aktual melewati ambang. Puncak adalah nilai tertinggi periode itu.")
            ep = episode(d, ambang)
            if ep.empty:
                st.write("Tidak ada hari di atas ambang pada data ini.")
            else:
                st.dataframe(ep, hide_index=True, height=300, column_config={"Puncak": st.column_config.NumberColumn(format="%.1f")})


# ====================== tab 3: cuaca dan musim ======================
@st.fragment
def tab_cuaca(prov):
    grup = "provinsi" if prov == SEMUA else "kota"
    grup_nama = "Provinsi" if grup == "provinsi" else "Kabupaten/kota"
    korelasi, bulanan, contoh = hitung_cuaca(prov, grup)
    warna = WARNA_PROVINSI if grup == "provinsi" else None
    intro("<b>Pertanyaan:</b> apakah PM2.5 cenderung naik atau turun bersamaan dengan kondisi cuaca tertentu? "
          "Yang terlihat adalah <i>pola yang berkaitan</i>, bukan bukti sebab-akibat."
          + ("" if grup == "provinsi" else " Karena satu provinsi dipilih, baris adalah 15 kabupaten/kota berpenduduk terbanyak."))

    with kotak("korelasi"):
        st.subheader("Korelasi PM2.5 dengan variabel cuaca")
        st.caption("Angka (r) dari -1 sampai +1. Merah: PM2.5 cenderung naik saat variabel itu naik. Biru: cenderung turun. "
                   "Mendekati 0: hampir tidak ada pola." + (" Tiap baris memakai rata-rata harian semua kabupaten/kota di provinsi itu." if grup == "provinsi" else ""))
        fig = px.imshow(korelasi, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
        fig.update_layout(coloraxis_colorbar=dict(title="r", thickness=12))
        fig.update_xaxes(side="top")
        st.plotly_chart(pakai_tema(fig, 130 + 46 * len(korelasi)))

    kiri, kanan = st.columns(2, gap="large")
    with kiri:
        with kotak("sebar_cuaca"):
            st.subheader("PM2.5 dan satu variabel cuaca")
            st.caption("Satu titik adalah satu hari di satu kabupaten/kota. Sebaran naik ke kanan berarti PM2.5 cenderung naik "
                       "bersama variabel itu.")
            var = st.selectbox("Variabel cuaca", list(CUACA), format_func=CUACA.get, key="an_var")
            fig2 = px.scatter(contoh, x=var, y="pm2_5", color=grup, opacity=0.55, color_discrete_map=warna,
                              labels={var: CUACA[var], "pm2_5": "PM2.5 (µg/m³)", grup: grup_nama})
            st.plotly_chart(pakai_tema(fig2, 340))
    with kanan:
        with kotak("bulanan"):
            st.subheader("Rata-rata PM2.5 per bulan")
            st.caption("Bulan bernilai tinggi menunjukkan musim polusi pada data ini.")
            st.markdown("<div style='height:4.6rem'></div>", unsafe_allow_html=True)
            fig3 = px.line(bulanan, x="bulan", y="pm2_5", color=grup, markers=True, color_discrete_map=warna,
                           labels={"bulan": "Bulan", "pm2_5": "PM2.5 (µg/m³)", grup: grup_nama})
            fig3.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=[b[:3] for b in BULAN])
            st.plotly_chart(pakai_tema(fig3, 340))


# ====================== halaman ======================
ev0 = evaluasi(SEMUA)
kepala(
    "Analitik dan evaluasi",
    "Untuk dosen dan tim peneliti: seberapa akurat model, di mana ia lemah, dan pola apa yang terlihat di data.",
    ([f"Sumber: data contoh (sintetis)"] if CONTOH else ["Sumber: file hasil tim"]) + [f"{ev0['n']:,} data evaluasi".replace(",", ".")],
)
c1, _ = st.columns([1, 3])
prov = c1.selectbox("Cakupan analisis", [SEMUA, *PROVINSI], key="an_prov")

ev = evaluasi(prov)
with kotak("temuan"):
    st.subheader("Temuan utama")
    st.caption("Ringkasan yang dihitung otomatis dari data untuk cakupan yang dipilih. Perlu dicek dan ditafsirkan oleh peneliti.")
    st.markdown('<ul class="rek">' + "".join(f"<li>{x}</li>" for x in temuan(ev, prov)) + "</ul>", unsafe_allow_html=True)

t1, t2, t3 = st.tabs(["Evaluasi model", "Tren & episode", "Cuaca & musim"], key="tab_analitik", on_change="rerun")
with t1:
    if t1.open:
        tab_evaluasi(prov)
with t2:
    if t2.open:
        tab_tren(prov)
with t3:
    if t3.open:
        tab_cuaca(prov)
