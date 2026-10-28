# Acuan Modeling dan Dashboard AirGuard SDGs

Dokumen ini menjadi acuan untuk tahap modeling dan pembuatan dashboard AirGuard SDGs. Tujuan utamanya adalah menghasilkan prediksi PM2.5 hari berikutnya untuk setiap kota dan menyajikan hasilnya dalam bentuk yang mudah dibaca.

## 1. Pertanyaan utama proyek

AirGuard diarahkan untuk menjawab pertanyaan berikut:

> Kota mana yang memiliki risiko PM2.5 paling tinggi, kapan polusi meningkat, dan seberapa baik kondisi sebelumnya membantu memprediksi polusi hari berikutnya?

Hasil analisis tidak boleh menyatakan hubungan sebab-akibat hanya berdasarkan korelasi. Gunakan istilah seperti “berkaitan dengan” atau “memiliki pola yang sama” jika belum ada analisis kausal.

## 2. Kondisi dataset

Dataset gabungan berisi data harian untuk 10 kota:

- Jakarta
- Surabaya
- Bandung
- Medan
- Semarang
- Makassar
- Palembang
- Yogyakarta
- Pontianak
- Banjarmasin

Data mencakup periode 1 Januari 2022 sampai 21 Oktober 2026. Variabel polusi mulai tersedia pada 4 Agustus 2022. Periode sebelumnya tidak digunakan untuk modeling polusi karena nilai polusinya kosong.

File yang digunakan untuk modeling:

```text
data/data_gabungan/airguard_preprocessed.csv
```

## 3. Target modeling

Target utama:

```text
target_pm2_5
```

Target tersebut berisi nilai PM2.5 pada hari berikutnya untuk kota yang sama.

Contoh:

| kota | tanggal | pm2_5 | target_pm2_5 |
|---|---|---:|---:|
| Jakarta | 2022-08-10 | 40.5 | 43.2 |

Artinya, model menggunakan informasi sampai 10 Agustus untuk memprediksi PM2.5 Jakarta pada 11 Agustus.

## 4. Fitur yang disiapkan

### Fitur waktu

- `tahun`
- `bulan`
- `hari_dalam_minggu`
- `hari_dalam_tahun`

### Fitur historis PM2.5

- `pm2_5`
- `pm2_5_lag_1`
- `pm2_5_lag_2`
- `pm2_5_lag_3`
- `pm2_5_lag_7`
- `pm2_5_rolling_3`
- `pm2_5_rolling_7`
- `pm2_5_rolling_14`

### Fitur cuaca

- `temperature_2m`
- `relative_humidity_2m`
- `precipitation`
- `wind_speed_10m`
- `wind_direction_10m`
- `surface_pressure`
- `cloud_cover`

Kolom `kota` tetap dipertahankan. Pada tahap modeling, kolom tersebut perlu diubah menjadi bentuk numerik, misalnya dengan one-hot encoding.

## 5. Variabel yang perlu diperlakukan hati-hati

### `us_aqi`

`us_aqi` sebaiknya tidak digunakan sebagai fitur utama untuk memprediksi PM2.5 karena AQI dihitung dari konsentrasi polutan. Menggunakannya dapat membuat model menerima informasi yang terlalu dekat dengan target.

Gunakan `us_aqi` untuk:

- Analisis EDA
- Label tingkat risiko
- Informasi tambahan pada dashboard

### Variabel polusi lain

`pm10`, `carbon_monoxide`, `nitrogen_dioxide`, `sulphur_dioxide`, dan `ozone` dapat digunakan sebagai fitur hanya jika nilai variabel tersebut memang tersedia pada waktu prediksi. Untuk eksperimen awal, gunakan PM2.5 historis dan variabel cuaca terlebih dahulu.

## 6. Model yang dibandingkan

Gunakan model pembanding sebelum memakai machine learning.

### Baseline

1. Persistence baseline: prediksi besok sama dengan PM2.5 hari ini.
2. Rolling baseline: prediksi besok sama dengan rata-rata PM2.5 tujuh hari terakhir.

### Model tree-based

Model yang disarankan:

1. `RandomForestRegressor`
2. `ExtraTreesRegressor`
3. `HistGradientBoostingRegressor`

Model tree-based sesuai untuk data ini karena dapat mempelajari hubungan nonlinear antara riwayat PM2.5, cuaca, waktu, dan kota. Model ini juga tidak membutuhkan standardisasi fitur seperti pada beberapa model berbasis jarak.

Jika library tambahan tersedia, XGBoost, LightGBM, atau CatBoost dapat digunakan sebagai eksperimen lanjutan. Model tambahan tidak wajib untuk tahap pertama.

## 7. Pembagian data

Jangan menggunakan pembagian data acak. Data memiliki urutan waktu, sehingga pembagian harus mengikuti kronologi.

Contoh pembagian:

- Training: 2022 sampai 2024
- Validasi: 2025
- Testing: 2026

Jika diperlukan, gunakan `TimeSeriesSplit` untuk validasi tambahan. Data masa depan tidak boleh masuk ke training.

## 8. Metrik evaluasi

Gunakan metrik berikut:

- MAE: rata-rata kesalahan absolut dalam satuan PM2.5. Gunakan sebagai metrik utama karena mudah dijelaskan.
- RMSE: memberikan penalti lebih besar terhadap kesalahan ekstrem.
- R2: menunjukkan seberapa besar variasi target yang dapat dijelaskan model.

Jangan menjadikan MAPE sebagai metrik utama karena PM2.5 dapat memiliki nilai rendah dan MAPE dapat menjadi tidak stabil.

Hasil evaluasi perlu dibandingkan dengan baseline. Model machine learning hanya dianggap berguna jika performanya lebih baik daripada baseline secara konsisten.

## 9. Output modeling

Modeling perlu menghasilkan beberapa output berikut.

### File prediksi

Nama file yang disarankan:

```text
data/data_gabungan/airguard_predictions.csv
```

Kolom minimal:

| Kolom | Keterangan |
|---|---|
| `kota` | Kota yang diprediksi |
| `tanggal_prediksi` | Tanggal target prediksi |
| `pm2_5_aktual` | Nilai sebenarnya pada data testing |
| `pm2_5_prediksi` | Hasil prediksi model |
| `error` | Selisih prediksi dan nilai aktual |
| `abs_error` | Nilai absolut dari error |
| `kategori_risiko` | Label risiko berdasarkan PM2.5 atau AQI |

Untuk prediksi masa depan, `pm2_5_aktual` dapat bernilai kosong sampai data aktual tersedia.

### File metrik model

Nama file yang disarankan:

```text
data/data_gabungan/model_metrics.csv
```

Kolom minimal:

```text
model, MAE, RMSE, R2
```

File ini digunakan untuk membandingkan baseline, Random Forest, Extra Trees, dan HistGradientBoosting.

### File feature importance

Nama file yang disarankan:

```text
data/data_gabungan/feature_importance.csv
```

Kolom minimal:

```text
feature, importance
```

Feature importance membantu menjelaskan apakah prediksi lebih banyak dipengaruhi oleh PM2.5 hari sebelumnya, rolling average, waktu, atau cuaca.

### File model tersimpan

Nama file yang disarankan:

```text
models/airguard_model.joblib
```

Simpan juga encoder atau pipeline preprocessing jika digunakan. Dashboard harus menggunakan pipeline yang sama dengan proses training.

## 10. Isi dashboard

Dashboard sebaiknya memiliki beberapa bagian berikut.

### Ringkasan kondisi terbaru

Tampilkan:

- PM2.5 terbaru setiap kota
- Prediksi PM2.5 hari berikutnya
- Perubahan dibandingkan hari sebelumnya
- Kategori risiko

### Peta kota

Gunakan koordinat `latitude` dan `longitude`. Warna marker dapat menunjukkan kategori risiko atau nilai PM2.5 terbaru.

### Ranking kota

Tampilkan kota berdasarkan:

- PM2.5 terbaru
- Prediksi PM2.5 tertinggi
- Rata-rata PM2.5 pada periode yang dipilih

### Tren historis

Sediakan filter kota dan rentang tanggal. Grafik minimal menampilkan:

- PM2.5 aktual
- Prediksi PM2.5
- Rata-rata bergerak jika diperlukan

### Episode polusi tinggi

Tampilkan tanggal ketika PM2.5 melewati ambang risiko yang dipilih. Jelaskan sumber ambang tersebut dalam laporan atau catatan dashboard.

### Penjelasan model

Tampilkan fitur yang paling berpengaruh berdasarkan `feature_importance.csv`. Hindari kalimat yang menyatakan bahwa fitur tersebut pasti menyebabkan polusi. Gunakan kalimat seperti “fitur yang paling banyak digunakan model dalam membuat prediksi”.

## 11. Kategori risiko

Kategori risiko harus memiliki sumber atau aturan yang jelas. Jangan membuat kategori baru tanpa dokumentasi.

Jika menggunakan kategori berbasis US AQI, simpan batas dan sumbernya dalam dokumentasi proyek. Jika kategori menggunakan ambang PM2.5, tuliskan bahwa kategori tersebut adalah aturan visualisasi proyek dan bukan klaim medis.

## 12. Pemeriksaan sebelum diserahkan

Modeling dianggap siap jika:

- Target tidak memiliki missing value.
- Tidak ada data masa depan yang masuk ke training.
- Lag dibuat per kota, bukan lintas kota.
- Rolling average tidak menggunakan nilai target masa depan.
- Model dikalahkan atau setidaknya dibandingkan secara jelas dengan baseline.
- MAE, RMSE, dan R2 tercatat untuk setiap model.
- Prediksi disimpan dalam file CSV.
- Model terbaik disimpan bersama pipeline encoding.
- Dashboard membaca file output yang benar.
- Nilai prediksi dan tanggal prediksi dapat dilacak kembali ke kota dan data asalnya.

## 13. Alur kerja singkat

```text
airguard_harian_semua_kota.csv
        ↓
EDA dan pemeriksaan missing value
        ↓
airguard_preprocessed.csv
        ↓
Pembuatan baseline dan fitur model
        ↓
Training model tree-based
        ↓
Evaluasi berdasarkan urutan waktu
        ↓
airguard_predictions.csv
        ↓
Dashboard dan interpretasi hasil
```

Fokus utama proyek adalah menghasilkan prediksi PM2.5 hari berikutnya yang dapat dibandingkan antar kota dan dapat dijelaskan kepada pengguna dashboard.
