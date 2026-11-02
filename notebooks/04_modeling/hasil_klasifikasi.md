# Progress Modeling: Hasil Klasifikasi

## 1. Status progress

Dokumen ini mencatat tahap awal modeling AirGuard.

Pada rancangan terbaru:

- Fokus modeling adalah klasifikasi tiga kategori risiko PM2.5.
- Target klasifikasi adalah `kategori_target_pm2_5`.
- Training dan evaluasi model belum dilakukan pada dokumen ini.

## 2. Dataset yang digunakan

Sumber data:

- Open-Meteo Air Quality API.
- Data berupa estimasi kualitas udara berbasis grid atmosfer dan koordinat wilayah.
- Data bukan pembacaan langsung dari sensor pada setiap kabupaten/kota.

Cakupan dataset:

| Informasi | Nilai |
|---|---:|
| Jumlah baris | 183.379 |
| Jumlah kolom awal | 16 |
| Jumlah kabupaten/kota | 119 |
| Periode awal | 2022-08-04 |
| Periode akhir | 2026-10-22 |
| Jumlah hari per wilayah | 1.541 |
| Missing value awal | 0 |
| Duplikasi wilayah-tanggal | 0 |

File sumber:

`data/data_gabungan/airguard_harian_kualitas_udara_jawa.csv`

Output preprocessing yang direncanakan:

`data/data_gabungan/airguard_preprocessed.csv`

## 3. Variabel awal dataset

### 3.1 Identitas wilayah

| Variabel | Keterangan |
|---|---|
| `kode_kabkota` | Kode administratif kabupaten/kota |
| `nama_kabkota` | Nama kabupaten/kota |
| `provinsi` | Provinsi |
| `tipe` | Jenis wilayah, misalnya kabupaten atau kota |

### 3.2 Informasi geografis

| Variabel | Keterangan |
|---|---|
| `latitude` | Garis lintang |
| `longitude` | Garis bujur |
| `elevasi_m` | Elevasi wilayah dalam meter |
| `luas_km2` | Luas wilayah |
| `penduduk` | Jumlah penduduk |

### 3.3 Informasi waktu

| Variabel | Keterangan |
|---|---|
| `tanggal` | Tanggal observasi |

### 3.4 Variabel kualitas udara

| Variabel | Keterangan |
|---|---|
| `pm2_5` | Konsentrasi PM2.5, target utama |
| `pm10` | Konsentrasi PM10 |
| `carbon_monoxide` | Konsentrasi karbon monoksida |
| `nitrogen_dioxide` | Konsentrasi nitrogen dioksida |
| `sulphur_dioxide` | Konsentrasi sulfur dioksida |
| `ozone` | Konsentrasi ozon |

## 4. Target modeling

Target utama adalah PM2.5 pada hari berikutnya untuk kabupaten/kota yang sama.

`target_pm2_5 = pm2_5 pada tanggal berikutnya`

Target dibuat menggunakan:

```python
df["target_pm2_5"] = (
    df.groupby("nama_kabkota")["pm2_5"]
      .shift(-1)
)
```

Contoh:

| Wilayah | Tanggal input | PM2.5 input | Target |
|---|---|---:|---:|
| Kota Bekasi | 2025-01-01 | 60,0 | PM2.5 tanggal 2025-01-02 |

Karena target yang digunakan adalah `kategori_target_pm2_5`, tahap modeling ini difokuskan pada klasifikasi multiclass. Target memiliki tiga kelas: Baik, Sedang, dan Tidak Sehat.

## 5. Feature engineering yang digunakan

### 5.1 Fitur lag PM2.5

Fitur lag menyimpan nilai PM2.5 pada satu hari tertentu di masa lalu.

| Variabel | Keterangan |
|---|---|
| `pm2_5_lag_1` | PM2.5 satu hari sebelumnya |
| `pm2_5_lag_2` | PM2.5 dua hari sebelumnya |
| `pm2_5_lag_3` | PM2.5 tiga hari sebelumnya |
| `pm2_5_lag_7` | PM2.5 tujuh hari sebelumnya |
| `pm2_5_lag_14` | PM2.5 empat belas hari sebelumnya |

Kode:

```python
for lag in [1, 2, 3, 7, 14]:
    df[f"pm2_5_lag_{lag}"] = (
        df.groupby("nama_kabkota")["pm2_5"]
          .shift(lag)
    )
```

### 5.2 Fitur rolling PM2.5

Rolling merupakan rata-rata PM2.5 pada beberapa hari terakhir.

| Variabel | Keterangan |
|---|---|
| `pm2_5_rolling_3` | Rata-rata PM2.5 tiga hari terakhir |
| `pm2_5_rolling_7` | Rata-rata PM2.5 tujuh hari terakhir |
| `pm2_5_rolling_14` | Rata-rata PM2.5 empat belas hari terakhir |

Kode:

```python
for window in [3, 7, 14]:
    df[f"pm2_5_rolling_{window}"] = (
        df.groupby("nama_kabkota")["pm2_5"]
          .transform(lambda x: x.rolling(window).mean())
    )
```

Perbedaan:

- Lag mengambil satu nilai pada hari tertentu.
- Rolling mengambil ringkasan rata-rata beberapa hari.
- Lag menunjukkan kondisi spesifik.
- Rolling menunjukkan kecenderungan atau tren.

### 5.3 Fitur kalender

Fitur kalender digunakan untuk menangkap pola harian, mingguan, dan tahunan.

| Variabel | Keterangan |
|---|---|
| `tahun` | Tahun observasi |
| `bulan` | Bulan observasi |
| `hari_dalam_minggu` | Hari dalam minggu, 0 sampai 6 |
| `hari_dalam_tahun` | Urutan hari dalam tahun |
| `akhir_pekan` | Penanda akhir pekan |

Kode:

```python
df["tahun"] = df["tanggal"].dt.year
df["bulan"] = df["tanggal"].dt.month
df["hari_dalam_minggu"] = df["tanggal"].dt.dayofweek
df["hari_dalam_tahun"] = df["tanggal"].dt.dayofyear
df["akhir_pekan"] = (
    df["hari_dalam_minggu"] >= 5
).astype(int)
```

### 5.4 Fitur kualitas udara lain

Variabel polutan lain digunakan sebagai fitur tambahan:

- `pm10`
- `carbon_monoxide`
- `nitrogen_dioxide`
- `sulphur_dioxide`
- `ozone`

Variabel cuaca belum digunakan pada dataset terbaru karena data final yang tersedia hanya berisi kualitas udara.

## 6. Daftar fitur prediksi sementara

```python
fitur_prediksi = [
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",

    "pm2_5_lag_1",
    "pm2_5_lag_2",
    "pm2_5_lag_3",
    "pm2_5_lag_7",
    "pm2_5_lag_14",

    "pm2_5_rolling_3",
    "pm2_5_rolling_7",
    "pm2_5_rolling_14",

    "tahun",
    "bulan",
    "hari_dalam_minggu",
    "hari_dalam_tahun",
    "akhir_pekan"
]

target = "target_pm2_5"
```

Kolom identitas seperti `nama_kabkota`, `provinsi`, dan `kode_kabkota` tetap disimpan untuk pelacakan hasil, tetapi tidak langsung digunakan sebagai fitur numerik.

## 7. Proses penghapusan baris awal dan akhir

Fitur lag dan rolling menghasilkan nilai kosong pada awal periode setiap wilayah. Target juga kosong pada tanggal terakhir setiap wilayah karena tidak ada data hari berikutnya.

```python
fitur_lag_rolling = [
    "pm2_5_lag_1",
    "pm2_5_lag_2",
    "pm2_5_lag_3",
    "pm2_5_lag_7",
    "pm2_5_lag_14",
    "pm2_5_rolling_3",
    "pm2_5_rolling_7",
    "pm2_5_rolling_14"
]

df_preprocessed = df.dropna(
    subset=fitur_lag_rolling + ["target_pm2_5"]
).reset_index(drop=True)
```

Baris tersebut bukan missing value pada data mentah. Baris tersebut tidak digunakan karena belum memiliki histori atau target yang lengkap.

## 8. Klasifikasi risiko

Klasifikasi merupakan target utama pada tahap modeling ini dan merepresentasikan kategori risiko PM2.5 hari berikutnya.

| Rentang PM2.5 | Kategori |
|---:|---|
| Ã¢â€°Â¤ 15 Ã‚Âµg/mÃ‚Â³ | Baik (Aman) |
| > 15 sampai 55 Ã‚Âµg/mÃ‚Â³ | Sedang (Waspada) |
| > 55 Ã‚Âµg/mÃ‚Â³ | Tidak Sehat (Bahaya) |

Kode:

```python
def label_risiko(pm25):
    if pm25 <= 15:
        return "Baik (Aman)"
    elif pm25 <= 55:
        return "Sedang (Waspada)"
    else:
        return "Tidak Sehat (Bahaya)"
```

Klasifikasi ini digunakan untuk:

- peta risiko besok
- tabel ranking
- jumlah wilayah berisiko tinggi
- warna status pada dashboard

Pada tahap ini, model memprediksi kategori risiko secara langsung. Forecasting regresi tidak termasuk fokus modeling saat ini.

## 9. Pembagian dataset berbasis waktu

Data dibagi menjadi tiga subset dengan urutan waktu. Random train-test split tidak digunakan karena dapat mencampurkan informasi masa depan ke dalam data training.

Rencana pembagian:

| Subset | Periode | Fungsi |
|---|---|---|
| Train | 2022-08-18 sampai 2024-12-31 | Melatih model |
| Validation | 2025-01-01 sampai 2025-12-31 | Memilih model dan tuning parameter |
| Test | 2026-01-01 sampai 2026-10-21 | Evaluasi akhir satu kali |

Setiap subset dibuat berdasarkan tanggal yang sama untuk seluruh kabupaten/kota. Target dan fitur pada test tidak digunakan saat training atau pemilihan model.

Pembagian ini lebih sesuai daripada split acak karena tujuan proyek adalah memprediksi kategori risiko pada periode mendatang.

## 10. Penanganan ketidakseimbangan kelas

Distribusi target secara keseluruhan:

| Kategori | Jumlah observasi |
|---|---:|
| Sedang (Waspada) | 118.774 |
| Tidak Sehat (Bahaya) | 35.858 |
| Baik (Aman) | 26.962 |

Kelas Sedang merupakan kelas mayoritas. Kelas Baik dan Tidak Sehat lebih sedikit. Selain imbalance, distribusi kelas juga dapat berubah antarperiode sehingga distribusi train, validation, dan test harus dilaporkan secara terpisah.

Strategi yang akan dibandingkan:

1. Model tanpa balancing sebagai baseline.
2. Class weight untuk memberi penalti lebih besar pada kelas minoritas.
3. SMOTE yang hanya diterapkan pada data train.

SMOTE tidak boleh diterapkan pada validation atau test. SMOTE juga harus dilakukan setelah split waktu dan hanya menggunakan fitur numerik yang tersedia pada data training.

Class weight menjadi pendekatan utama yang lebih aman untuk data deret waktu. SMOTE digunakan sebagai eksperimen pembanding karena data sintetis dapat kurang merepresentasikan pola temporal atau karakteristik wilayah sebenarnya.

## 11. Rencana model klasifikasi

Fokus model hanya pada klasifikasi tiga kelas:

1. **LightGBM Classifier**
   - Kandidat model utama.
   - Cocok untuk data tabular berukuran besar.
   - Dapat menangkap pola non-linear.
   - Dapat menggunakan pembobotan kelas.

2. **Extra Trees Classifier**
   - Model ensemble berbasis pohon.
   - Tidak memerlukan standardisasi fitur.
   - Dapat menggunakan `class_weight="balanced"`.

3. **HistGradientBoosting Classifier**
   - Model boosting untuk data tabular.
   - Dapat menangkap hubungan non-linear.
   - Digunakan sebagai pembanding.

Baseline tambahan:

- Dummy Classifier.
- Prediksi kategori berdasarkan kategori PM2.5 hari sebelumnya.

## 12. Metrik evaluasi

Accuracy tidak digunakan sebagai satu-satunya metrik karena kelas Sedang dominan.

Metrik yang dicatat:

- Precision per kelas.
- Recall per kelas.
- F1-score per kelas.
- Macro F1-score.
- Balanced accuracy.
- Confusion matrix.

Fokus interpretasi:

- Recall kelas Baik: seberapa banyak kondisi Baik yang berhasil dikenali.
- Recall kelas Tidak Sehat: seberapa banyak kondisi berbahaya yang berhasil dideteksi.
- Macro F1: keseimbangan performa pada seluruh kelas.

## 13. Pencegahan data leakage

- Lag dan rolling dihitung per kabupaten/kota.
- Fitur hanya menggunakan data saat ini dan masa lalu.
- Nilai target tidak digunakan sebagai fitur.
- Data masa depan tidak boleh masuk ke proses training.
- Scaler hanya di-fit menggunakan data training.
- Pembagian data dilakukan berdasarkan waktu, bukan random split.
- US AQI tidak digunakan sebagai fitur karena terlalu dekat dengan PM2.5.

## 14. Status pekerjaan saat ini

### Sudah tersedia

- Dataset kualitas udara Pulau Jawa.
- Pemeriksaan missing value.
- Pemeriksaan duplikasi wilayah-tanggal.
- Pemeriksaan kelengkapan periode.
- EDA distribusi dan korelasi.
- Fitur lag PM2.5.
- Fitur rolling PM2.5.
- Target PM2.5 hari berikutnya.
- Rancangan kategori risiko.

### Masih akan dikerjakan

- Memastikan file preprocessing final tersimpan.
- Membuat persistence baseline.
- Membuat rolling mean baseline.
- Melatih LightGBM Regressor.
- Melatih Extra Trees Regressor.
- Melatih HistGradientBoosting Regressor.
- Mengevaluasi MAE, RMSE, dan RÃ‚Â².
- Menyimpan hasil prediksi dan feature importance.
- Menghubungkan output modeling ke dashboard.

## 15. File output modeling yang direncanakan

- `data/data_gabungan/airguard_preprocessed.csv`
- `data/data_gabungan/airguard_predictions.csv`
- `data/data_gabungan/model_metrics.csv`
- `data/data_gabungan/feature_importance.csv`
- `models/airguard_model.joblib`

Dokumen ini akan diperbarui setelah tahap modeling dan evaluasi klasifikasi selesai.

## 16. Alur kerja dan handoff modeling

Alur lengkap proyek klasifikasi risiko PM2.5:

```text
Dataset kualitas udara
        ↓
Pemeriksaan data
        ↓
EDA
        ↓
Preprocessing
        ↓
Feature engineering
        ↓
Menentukan target klasifikasi
        ↓
Split data berbasis waktu
        ↓
HANDOFF KE TAHAP MODELING
        ↓
Encoding target
        ↓
Penanganan imbalance
        ↓
Training model
        ↓
Evaluasi model
        ↓
Pemilihan model terbaik
        ↓
Penyimpanan hasil untuk dashboard
```

### 16.1 Pekerjaan yang sudah selesai

- Dataset kualitas udara Pulau Jawa berhasil dibaca.
- Missing value dan duplikasi wilayah-tanggal telah diperiksa.
- EDA distribusi, korelasi, tren, dan distribusi risiko telah dilakukan.
- Fitur lag PM2.5 telah tersedia.
- Fitur rolling PM2.5 telah tersedia.
- Fitur kalender dibuat pada notebook modeling.
- Target klasifikasi `kategori_target_pm2_5` telah ditentukan.
- Fitur dan target telah dipisahkan menjadi `X` dan `y`.
- Data telah dibagi berdasarkan waktu menjadi train, validation, dan test.

### 16.2 Pembagian data yang digunakan

| Subset | Periode | Fungsi |
|---|---|---|
| Train | 2022-08-18 sampai 2024-12-31 | Melatih model |
| Validation | 2025-01-01 sampai 2025-12-31 | Memilih model dan tuning |
| Test | 2026-01-01 sampai 2026-10-21 | Evaluasi akhir |

Variabel hasil split yang tersedia:

```python
X_train, y_train
X_val, y_val
X_test, y_test
```

### 16.3 Pekerjaan yang belum dilakukan

Tahap berikutnya menjadi tanggung jawab modeling:

- Encoding label target.
- Pemeriksaan distribusi kelas pada setiap subset.
- Pembuatan baseline.
- Training model tanpa balancing.
- Training model dengan class weight.
- Eksperimen SMOTE hanya pada data train.
- Feature selection jika diperlukan.
- Training LightGBM Classifier.
- Training Extra Trees Classifier.
- Training HistGradientBoosting Classifier.
- Evaluasi precision, recall, F1-score, macro F1, balanced accuracy, dan confusion matrix.
- Pemilihan model terbaik berdasarkan validation.
- Evaluasi final satu kali pada data test.
- Penyimpanan prediksi, metrik, dan feature importance untuk dashboard.

### 16.4 Batasan penting untuk tahap modeling

- Jangan menggunakan random train-test split.
- Jangan menerapkan SMOTE pada validation atau test.
- Jangan memasukkan `target_pm2_5` atau `kategori_target_pm2_5` ke dalam fitur.
- Jangan menggunakan informasi dari periode test saat tuning model.
- Gunakan macro F1 dan recall per kelas, bukan accuracy saja.
- Perhatikan recall kelas Baik dan Tidak Sehat karena keduanya lebih sedikit dibanding kelas Sedang.


