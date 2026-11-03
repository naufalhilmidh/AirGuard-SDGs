"""Peta batas wilayah untuk halaman EWS.

Batas kabupaten/kota dibaca dari referensi/batas_kabkota_jawa.geojson (dibuat oleh referensi/buat_batas.py
di dashboard pertama). Tiap poligon digambar sebagai go.Scatter dengan fill="toself" (SVG biasa, bukan
WebGL), jadi warnanya selalu tampil dan hover, geser, serta zoom tetap berfungsi. Warna diberikan literal
per wilayah dari Python, sehingga pasti sama dengan legenda.
"""
import json
import math
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

BERKAS = Path(__file__).parent / "referensi" / "batas_kabkota_jawa.geojson"
KONFIG_PETA = {"displaylogo": False, "scrollZoom": False, "modeBarButtonsToRemove": ["select2d", "lasso2d", "toImage"]}
ABU = "#D8DEE9"


@st.cache_resource(show_spinner=False)
def lapisan():
    """Daftar (kode, nama, x, y) per cincin poligon. None kalau berkas batas belum ada.

    x dikali cos(lintang tengah) supaya bentuk Pulau Jawa tidak melebar."""
    if not BERKAS.exists():
        return None
    fitur = json.loads(BERKAS.read_text(encoding="utf-8"))["features"]
    kx = math.cos(math.radians(-7.3))
    hasil = []
    for f in fitur:
        g = f["geometry"]
        polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for p in polis:
            ring = p[0]  # cincin luar saja; lubang tidak berarti untuk peta ini
            xs, ys, terakhir = [], [], None
            for lon, lat in ring:
                x, y = lon * kx, lat
                if terakhir and math.hypot(x - terakhir[0], y - terakhir[1]) < 0.004:  # sekitar 400 m
                    continue
                xs.append(round(x, 4))
                ys.append(round(y, 4))
                terakhir = (x, y)
            if len(xs) > 3:
                hasil.append((f["properties"].get("kode"), f["properties"].get("nama", ""), xs, ys))
    return hasil


def tersedia() -> bool:
    return BERKAS.exists()


def gambar(warna: dict, tips: dict, pilih=None, batas=None, tinggi=360, kunci="peta"):
    """warna dan tips: kode BPS -> warna hex / teks hover. pilih: kode wilayah yang diberi garis tebal."""
    fig = go.Figure()
    for kode, nama, xs, ys in lapisan():
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", fill="toself", fillcolor=warna.get(kode, ABU),
            line=dict(color="#FFFFFF", width=0.5), hoveron="fills", text=tips.get(kode, nama),
            hovertemplate="%{text}<extra></extra>", showlegend=False,
            hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#CBD5E1", align="left",
                            font=dict(family="Inter, sans-serif", size=12, color="#0F172A"))))
    if pilih:
        for kode, nama, xs, ys in lapisan():
            if kode == pilih:
                fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#1E3A8A", width=3),
                                         hoverinfo="skip", showlegend=False))
    sumbu_x, sumbu_y = dict(visible=False), dict(visible=False, scaleanchor="x", scaleratio=1)
    if batas:  # zoom ke wilayah yang sedang ditampilkan
        sub = [(xs, ys) for kode, _, xs, ys in lapisan() if kode in batas]
        x0, x1 = min(min(x) for x, _ in sub), max(max(x) for x, _ in sub)
        y0, y1 = min(min(y) for _, y in sub), max(max(y) for _, y in sub)
        pad = max(x1 - x0, y1 - y0) * 0.06
        sumbu_x["range"], sumbu_y["range"] = [x0 - pad, x1 + pad], [y0 - pad, y1 + pad]
    fig.update_layout(
        height=tinggi, showlegend=False, dragmode="pan", hovermode="closest", margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", uirevision=kunci,
        xaxis=sumbu_x, yaxis=sumbu_y)  # skala dikunci agar pulau tidak gepeng
    return fig
