# Dashboard AirGuard SDGs (gabungan)

Satu dashboard Streamlit dengan tampilan hijau milik dashboard 1 (landing, sidebar filter, tab), ditambah semua fitur dashboard EWS.

## Menjalankan
```
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```
Untuk deploy di Streamlit Cloud: main file `dashboard/app.py`.

## Tab
- **Ringkasan**: kartu ringkas, jumlah kab/kota per status besok, status kota-kota besar, kartu detail per daerah (pilih daerah, rekomendasi), unduh CSV status besok, peta risiko atau zona cluster, peringkat.
- **Tren & Prediksi**: aktual vs prediksi, selisih, episode polusi tinggi.
- **Proyeksi 2027**: kalender risiko bulanan, tren sampai akhir tahun depan, rekomendasi, unduh CSV.
- **Faktor Lain**: korelasi PM2.5 dengan polutan lain.
- **Klaster wilayah**: tiga zona K-Means, sebaran, per provinsi, tabel.
- **Model**: evaluasi pada data uji (sejak 1 Jan 2026): MAE, RMSE, R2, bias, metrik 3 status, confusion matrix, galat per provinsi dan bulan.

## Status (3 tingkat)
Baik sampai 15, Sedang 15,1 sampai 55, Tidak sehat di atas 55 ug/m3. Diatur di `utils.py` (`KATEGORI`).

## Sumber data (tidak pernah dicampur)
Urutan: file tim di `data/data_gabungan`, lalu baseline dari data asli, lalu data contoh.

| Kondisi | Mode | Keterangan |
|---|---|---|
| `airguard_predictions.csv` ada | tim | prediksi dari model tim |
| hanya `airguard_preprocessed.csv` | baseline | prediksi besok = hari ini (persistence), ditandai di dashboard |
| tidak ada file tim | contoh | data sintetis di `dashboard/sample` |

File opsional: `model_metrics.csv`, `feature_importance.csv` (tab Model), `clustering_wilayah.csv` (tab Klaster dan peta zona), `airguard_forecast.csv` (proyeksi dari model; kolom `kota`/`kode_kabkota`, `tanggal`, `pm2_5_prakiraan`, opsional `batas_bawah`, `batas_atas`). Tanpa file forecast, proyeksi memakai pola musiman historis dan diberi label itu.

## Catatan data
- Data CAMS beresolusi grid: dari 119 kab/kota hanya 63 deret PM2.5 yang berbeda.
- Data asli belum memuat variabel cuaca, jadi tab Faktor Lain memakai polutan lain dan riwayat PM2.5.
