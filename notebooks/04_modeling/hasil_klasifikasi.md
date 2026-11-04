# Progress Modeling: Hasil Klasifikasi

## 1. Status progress

Dokumen ini mencatat hasil modeling klasifikasi risiko PM2.5 pada proyek AirGuard.

Status saat ini:

- Fokus modeling adalah klasifikasi tiga kategori risiko PM2.5 hari berikutnya.
- Target klasifikasi adalah `kategori_target_pm2_5`.
- Training, pemilihan model, dan evaluasi akhir pada data test sudah selesai.
- Pembagian data sudah diperbaiki. Versi sebelumnya salah mengambil baris karena `X` dan `y` dibuat sebelum `df` diurutkan ulang. Semua angka di dokumen ini berasal dari notebook versi perbaikan.
- Hasil prediksi, metrik, dan feature importance belum disimpan ke file (lihat Bagian 15).

Ringkasan hasil:

| Item | Nilai |
|---|---|
| Model terpilih | LightGBM dengan class weight |
| Macro F1 validation | 0,7381 |
| Macro F1 test | 0,7613 |
| Accuracy test | 0,8210 |
| Recall Tidak Sehat pada test | 0,7938 |
| Recall Baik pada test | 0,6796 |

Keunggulan model atas baseline persistence kecil pada macro F1 (selisih 0,0044 pada validation). Model lebih baik pada recall kelas Baik dan Tidak Sehat. Penjelasan lengkap ada di Bagian 12.

## 2. Dataset yang digunakan

Sumber data:

- Open-Meteo Air Quality API.
- Data berupa estimasi kualitas udara berbasis grid atmosfer dan koordinat wilayah.
- Data bukan pembacaan langsung dari sensor pada setiap kabupaten/kota.

Cakupan dataset:

| Informasi | Data mentah | Data setelah preprocessing |
|---|---:|---:|
| Jumlah baris | 183.379 | 181.594 |
| Jumlah kolom | 16 | 26 |
| Jumlah kabupaten/kota | 119 | 119 |
| Jumlah provinsi | 6 | 6 |
| Periode awal | 2022-08-04 | 2022-08-18 |
| Periode akhir | 2026-10-22 | 2026-10-21 |
| Jumlah hari per wilayah | 1.541 | 1.526 |
| Missing value | 0 | 0 |
| Duplikasi wilayah-tanggal | 0 | 0 |

Selisih 1.785 baris berasal dari 15 baris per wilayah (119 x 15). Empat belas baris awal hilang karena lag 14 hari. Satu baris akhir hilang karena tidak ada target hari berikutnya.

File sumber:

`data/data_gabungan/airguard_harian_kualitas_udara_jawa.csv`

File hasil preprocessing:

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
| `pm2_5` | Konsentrasi PM2.5 |
| `pm10` | Konsentrasi PM10 |
| `carbon_monoxide` | Konsentrasi karbon monoksida |
| `nitrogen_dioxide` | Konsentrasi nitrogen dioksida |
| `sulphur_dioxide` | Konsentrasi sulfur dioksida |
| `ozone` | Konsentrasi ozon |

## 4. Target modeling

Target adalah kategori risiko PM2.5 pada hari berikutnya untuk kabupaten/kota yang sama.

Nilai PM2.5 hari berikutnya dibuat dengan kode ini:

```python
df["target_pm2_5"] = (
    df.groupby("nama_kabkota")["pm2_5"]
      .shift(-1)
)
```

Nilai itu lalu diubah menjadi `kategori_target_pm2_5` memakai ambang pada Bagian 8.

Contoh dari data (Kabupaten Administrasi Kepulauan Seribu):

| Tanggal input | PM2.5 input | PM2.5 hari berikutnya | Kategori target |
|---|---:|---:|---|
| 2022-08-18 | 22,03 | 21,33 | Sedang (Waspada) |

PM2.5 hari berikutnya (21,33) sama dengan PM2.5 pada baris tanggal 2022-08-19. Ini menunjukkan target dibuat dengan benar.

Tahap modeling ini memakai klasifikasi multiclass dengan tiga kelas: Baik, Sedang, dan Tidak Sehat.

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

Rolling adalah rata-rata PM2.5 pada beberapa hari terakhir.

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
- Rolling mengambil rata-rata beberapa hari.
- Lag menunjukkan kondisi spesifik.
- Rolling menunjukkan kecenderungan jangka pendek.

### 5.3 Fitur kalender

Fitur kalender dibuat di notebook modeling, setelah data diurutkan berdasarkan tanggal dan wilayah.

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

Polutan lain dipakai sebagai fitur tambahan:

- `pm10`
- `carbon_monoxide`
- `nitrogen_dioxide`
- `sulphur_dioxide`
- `ozone`

Variabel cuaca belum dipakai karena data final hanya berisi kualitas udara.

### 5.5 Fitur geografis

Lima variabel geografis ikut menjadi fitur: `latitude`, `longitude`, `elevasi_m`, `luas_km2`, dan `penduduk`. Nilainya tetap untuk setiap wilayah. Model dapat memakainya untuk mengenali wilayah.

## 6. Daftar fitur model

Model memakai 24 fitur:

```python
fitur_model = [
    # Geografis
    "latitude", "longitude", "elevasi_m", "luas_km2", "penduduk",

    # Kualitas udara saat ini
    "pm2_5", "pm10", "carbon_monoxide",
    "nitrogen_dioxide", "sulphur_dioxide", "ozone",

    # Lag
    "pm2_5_lag_1", "pm2_5_lag_2", "pm2_5_lag_3",
    "pm2_5_lag_7", "pm2_5_lag_14",

    # Rolling
    "pm2_5_rolling_3", "pm2_5_rolling_7", "pm2_5_rolling_14",

    # Kalender
    "tahun", "bulan", "hari_dalam_minggu",
    "hari_dalam_tahun", "akhir_pekan"
]

target = "kategori_target_pm2_5"
```

Kolom identitas seperti `nama_kabkota`, `provinsi`, `kode_kabkota`, dan `tipe` disimpan untuk pelacakan hasil. Model tidak memakainya sebagai fitur.

## 7. Penghapusan baris awal dan akhir

Lag dan rolling menghasilkan nilai kosong pada awal periode setiap wilayah. Target kosong pada tanggal terakhir setiap wilayah.

```python
fitur_lag_rolling = [
    "pm2_5_lag_1", "pm2_5_lag_2", "pm2_5_lag_3",
    "pm2_5_lag_7", "pm2_5_lag_14",
    "pm2_5_rolling_3", "pm2_5_rolling_7", "pm2_5_rolling_14"
]

df_preprocessed = df.dropna(
    subset=fitur_lag_rolling + ["target_pm2_5"]
).reset_index(drop=True)
```

Baris ini bukan missing value pada data mentah. Model tidak memakainya karena histori atau target belum lengkap. Totalnya 1.785 baris (lihat Bagian 2).

## 8. Klasifikasi risiko

Kategori risiko dibuat dari nilai PM2.5 dengan ambang berikut.

| Rentang PM2.5 | Kategori |
|---:|---|
| ≤ 15 µg/m³ | Baik (Aman) |
| > 15 sampai 55 µg/m³ | Sedang (Waspada) |
| > 55 µg/m³ | Tidak Sehat (Bahaya) |

Kode:

```python
def label_risiko(pm25):
    if pm25 <= 15:
        return "Baik (Aman)"
    elif pm25 <= 55:
        return "Sedang (Waspada)"
    return "Tidak Sehat (Bahaya)"
```

Hasil klasifikasi dipakai untuk:

- peta risiko besok
- tabel ranking
- jumlah wilayah berisiko tinggi
- warna status pada dashboard

Model memprediksi kategori risiko secara langsung. Regresi PM2.5 tidak termasuk dalam tahap ini.

Label encoding yang dipakai model:

| Kategori | Kode |
|---|---:|
| Baik (Aman) | 0 |
| Sedang (Waspada) | 1 |
| Tidak Sehat (Bahaya) | 2 |

## 9. Pembagian dataset berbasis waktu

Data dibagi menurut waktu. Random split tidak dipakai karena dapat membawa informasi masa depan ke data training.

| Subset | Periode | Jumlah baris | Fungsi |
|---|---|---:|---|
| Train | 2022-08-18 sampai 2024-12-31 | 103.173 | Melatih model |
| Validation | 2025-01-01 sampai 2025-12-31 | 43.435 | Memilih model |
| Test | 2026-01-01 sampai 2026-10-21 | 34.986 | Evaluasi akhir satu kali |

Setiap subset memakai tanggal yang sama untuk semua kabupaten/kota. Test hanya dipakai satu kali, setelah model terpilih.

Notebook memeriksa pembagian ini dengan `assert`. Pemeriksaan memastikan tanggal setiap subset sesuai rencana dan tidak ada tumpang tindih waktu. Semua pemeriksaan lolos.

## 10. Penanganan ketidakseimbangan kelas

### 10.1 Distribusi kelas

Distribusi seluruh data:

| Kategori | Jumlah | Persentase |
|---|---:|---:|
| Sedang (Waspada) | 118.774 | 65,41% |
| Tidak Sehat (Bahaya) | 35.858 | 19,75% |
| Baik (Aman) | 26.962 | 14,85% |

Distribusi per subset:

| Subset | Baik (Aman) | Sedang (Waspada) | Tidak Sehat (Bahaya) |
|---|---:|---:|---:|
| Train | 23.145 (22,43%) | 69.327 (67,19%) | 10.701 (10,37%) |
| Validation | 2.147 (4,94%) | 26.833 (61,78%) | 14.455 (33,28%) |
| Test | 1.670 (4,77%) | 22.614 (64,64%) | 10.702 (30,59%) |

Distribusi per tahun:

| Tahun | Baik (Aman) | Sedang (Waspada) | Tidak Sehat (Bahaya) |
|---|---:|---:|---:|
| 2022 | 29,20% | 63,95% | 6,85% |
| 2023 | 21,52% | 69,68% | 8,80% |
| 2024 | 20,83% | 65,92% | 13,25% |
| 2025 | 4,94% | 61,78% | 33,28% |
| 2026 | 4,77% | 64,64% | 30,59% |

### 10.2 Pergeseran distribusi

Distribusi kelas berubah besar antara train dan dua subset lainnya.

- Kelas Baik turun dari 22,43% pada train menjadi 4,94% pada validation dan 4,77% pada test.
- Kelas Tidak Sehat naik dari 10,37% pada train menjadi 33,28% pada validation dan 30,59% pada test.
- Perubahan terjadi pada tahun 2025, bukan bertahap.

Penyebab perubahan ini belum diselidiki. Perubahan bisa berasal dari kondisi udara yang memang memburuk, atau dari perubahan pada data sumber. Cek ini perlu dilakukan sebelum hasil dipakai sebagai dasar keputusan.

Dampaknya pada model:

- Model dilatih pada data dengan lebih banyak hari Baik dan lebih sedikit hari Tidak Sehat.
- Model diuji pada data dengan pola sebaliknya.
- Presisi kelas Baik pada test (0,6309) sangat mungkin terpengaruh, karena kelas ini jarang pada test.

### 10.3 Strategi yang dibandingkan

1. Tanpa balancing sebagai baseline.
2. Class weight `balanced`. Untuk HistGradientBoosting, bobot diberikan lewat `sample_weight`.
3. SMOTE hanya pada data train. Jumlah train naik dari `[23.145, 69.327, 10.701]` menjadi `[69.327, 69.327, 69.327]`.

SMOTE tidak dipakai pada validation dan test.

## 11. Model klasifikasi

Tiga model dibandingkan:

1. **LightGBM Classifier**: `n_estimators=300`, `learning_rate=0,05`, `num_leaves=63`.
2. **Extra Trees Classifier**: `n_estimators=300`, `min_samples_leaf=2`.
3. **HistGradientBoosting Classifier**: `max_iter=300`, `learning_rate=0,05`.

Semua model memakai `random_state=42`. Hyperparameter belum di-tuning. Nilai di atas adalah pengaturan tetap.

Baseline:

- **Dummy Classifier**: selalu memprediksi kelas mayoritas.
- **Persistence kategori**: memprediksi kategori besok sama dengan kategori PM2.5 hari ini.

## 12. Hasil evaluasi

Metrik yang dicatat: accuracy, balanced accuracy, macro F1, serta recall dan F1 per kelas. Accuracy tidak dipakai sendirian karena kelas Sedang dominan.

### 12.1 Hasil pada validation

Diurutkan menurut macro F1.

| Model | Strategi | Accuracy | Balanced acc. | Macro F1 | Recall Baik | Recall Sedang | Recall Tidak Sehat |
|---|---|---:|---:|---:|---:|---:|---:|
| **LightGBM** | **Class weight** | **0,7874** | **0,7490** | **0,7381** | **0,6577** | **0,7929** | **0,7963** |
| Persistence | Baseline | 0,7916 | 0,7336 | 0,7337 | 0,6274 | 0,8315 | 0,7420 |
| HistGB | Class weight | 0,7812 | 0,7506 | 0,7326 | 0,6656 | 0,7734 | 0,8129 |
| HistGB | SMOTE | 0,7817 | 0,7318 | 0,7309 | 0,6288 | 0,8042 | 0,7624 |
| ExtraTrees | SMOTE | 0,7848 | 0,7446 | 0,7309 | 0,6646 | 0,8062 | 0,7629 |
| LightGBM | SMOTE | 0,7781 | 0,7311 | 0,7286 | 0,6162 | 0,7819 | 0,7951 |
| HistGB | Tanpa balancing | 0,7935 | 0,7000 | 0,7262 | 0,5566 | 0,8854 | 0,6580 |
| LightGBM | Tanpa balancing | 0,7959 | 0,6972 | 0,7261 | 0,5380 | 0,8849 | 0,6688 |
| ExtraTrees | Class weight | 0,7816 | 0,7010 | 0,7176 | 0,6218 | 0,9049 | 0,5765 |
| ExtraTrees | Tanpa balancing | 0,7862 | 0,6865 | 0,7158 | 0,5673 | 0,9178 | 0,5745 |
| Dummy | Kelas mayoritas | 0,6178 | 0,3333 | 0,2546 | 0,0000 | 1,0000 | 0,0000 |

### 12.2 Temuan pada validation

- LightGBM dengan class weight punya macro F1 tertinggi (0,7381).
- Selisihnya dengan HistGB class weight (0,7326) dan persistence (0,7337) kecil. Validation hanya mencakup satu tahun, jadi selisih sekecil ini belum cukup untuk menyatakan satu model unggul secara pasti.
- Persistence adalah baseline yang kuat. Kategori hari ini sudah memprediksi kategori besok dengan akurasi 79,16%.
- Class weight dan SMOTE menaikkan recall kelas Baik dan Tidak Sehat pada hampir semua model dibanding tanpa balancing.
- Class weight menurunkan recall kelas Sedang. Ini harga yang wajar untuk deteksi kelas minoritas.
- Class weight sedikit lebih baik daripada SMOTE pada macro F1 untuk LightGBM dan HistGB. Hasil ini sejalan dengan rencana awal yang menjadikan class weight sebagai pendekatan utama.
- ExtraTrees memberi hasil terendah di antara tiga model pada kondisi tanpa balancing dan class weight.

Perbandingan model terpilih dengan persistence pada validation:

| Metrik | LightGBM class weight | Persistence | Selisih |
|---|---:|---:|---:|
| Macro F1 | 0,7381 | 0,7337 | +0,0044 |
| Balanced accuracy | 0,7490 | 0,7336 | +0,0154 |
| Accuracy | 0,7874 | 0,7916 | -0,0042 |
| Recall Baik | 0,6577 | 0,6274 | +0,0303 |
| Recall Sedang | 0,7929 | 0,8315 | -0,0386 |
| Recall Tidak Sehat | 0,7963 | 0,7420 | +0,0543 |

Keunggulan model terlihat paling jelas pada recall Tidak Sehat. Untuk sistem peringatan, ini metrik yang paling penting.

### 12.3 Model terpilih

Model terpilih berdasarkan macro F1 pada validation: **LightGBM dengan class weight**.

### 12.4 Hasil akhir pada test

Evaluasi dilakukan satu kali pada data test (2026-01-01 sampai 2026-10-21).

| Kelas | Precision | Recall | F1-score | Jumlah data |
|---|---:|---:|---:|---:|
| Baik (Aman) | 0,6309 | 0,6796 | 0,6544 | 1.670 |
| Sedang (Waspada) | 0,8744 | 0,8443 | 0,8591 | 22.614 |
| Tidak Sehat (Bahaya) | 0,7483 | 0,7938 | 0,7703 | 10.702 |

| Metrik keseluruhan | Nilai |
|---|---:|
| Accuracy | 0,8210 |
| Balanced accuracy (macro recall) | 0,7726 |
| Macro F1 | 0,7613 |
| Weighted F1 | 0,8222 |

Interpretasi:

- Model mendeteksi 79,38% hari Tidak Sehat dan 67,96% hari Baik.
- Kelas Sedang paling mudah diprediksi (F1 0,8591).
- Kelas Baik paling sulit (F1 0,6544). Kelas ini hanya 4,77% dari data test.
- Metrik test lebih tinggi daripada validation. Periode test lebih pendek dan tidak mencakup November dan Desember, jadi kedua angka tidak sepenuhnya sebanding.

Matriks kebingungan sudah dibuat di notebook (jumlah dan persentase per kelas aktual). Angkanya belum disalin ke dokumen ini.

### 12.5 Batas kesimpulan

- Persistence belum dievaluasi pada test. Karena itu dokumen ini belum bisa menyatakan bahwa model mengalahkan baseline pada test.
- Pergeseran distribusi kelas (Bagian 10.2) membuat performa pada periode berikutnya sulit diperkirakan.
- Hyperparameter belum di-tuning.
- Evaluasi belum dipecah per wilayah atau per provinsi.

## 13. Pencegahan data leakage

- Lag dan rolling dihitung per kabupaten/kota.
- Fitur hanya memakai data hari ini dan masa lalu.
- Target tidak dipakai sebagai fitur.
- Pembagian data berdasarkan waktu, bukan random split.
- `X` dan `y` diambil langsung dari `df` yang sudah diurutkan, tanpa bergantung pada index lama.
- Notebook memakai `assert` untuk memastikan periode subset benar dan tidak tumpang tindih.
- SMOTE hanya dijalankan pada data train.
- Pemilihan model memakai validation. Test dipakai satu kali.
- US AQI tidak dipakai sebagai fitur karena terlalu dekat dengan PM2.5.
- Notebook belum memakai scaler. Model berbasis pohon tidak memerlukannya.

Satu risiko yang masih ada: fitur `tahun`. Data train hanya berisi 2022 sampai 2024, sedangkan validation dan test berisi 2025 dan 2026. Model berbasis pohon tidak dapat mempelajari nilai tahun yang belum pernah muncul. Pengaruh fitur ini perlu diuji (Bagian 14).

## 14. Pekerjaan lanjutan

### Sudah selesai

- Dataset kualitas udara Pulau Jawa dibaca dan diperiksa.
- Missing value dan duplikasi wilayah-tanggal diperiksa.
- EDA distribusi, korelasi, tren, dan distribusi risiko.
- Fitur lag, rolling, dan kalender.
- Target klasifikasi.
- Split berbasis waktu dengan pemeriksaan otomatis.
- Encoding label.
- Baseline Dummy dan persistence.
- Training tiga model dengan tiga strategi imbalance.
- Pemilihan model pada validation.
- Evaluasi akhir pada test.

### Belum dikerjakan

1. Evaluasi baseline persistence pada test sebagai pembanding laporan. Hasilnya tidak boleh dipakai untuk memilih model.
2. Selidiki perubahan distribusi kelas pada tahun 2025.
3. Uji model tanpa fitur `tahun` pada validation.
4. Tuning hyperparameter LightGBM pada validation.
5. Hitung feature importance sebagai angka dan simpan ke file. Notebook baru menampilkan grafik.
6. Salin angka confusion matrix ke dokumen ini.
7. Evaluasi performa per provinsi dan per kabupaten/kota.
8. Simpan prediksi, metrik, dan model untuk dashboard (Bagian 15).
9. Hubungkan output ke dashboard.

Catatan teknis: pemeriksaan kolom di notebook (Cell 24) berjalan sebelum fitur kalender dibuat. Hasilnya melaporkan lima kolom kalender sebagai belum tersedia. Ini bukan error data. Pindahkan cell tersebut ke setelah fitur kalender dibuat agar hasilnya tidak membingungkan.

## 15. File output modeling

| File | Status |
|---|---|
| `data/data_gabungan/airguard_preprocessed.csv` | Tersedia |
| `data/data_gabungan/airguard_predictions.csv` | Belum dibuat |
| `data/data_gabungan/model_metrics.csv` | Belum dibuat |
| `data/data_gabungan/feature_importance.csv` | Belum dibuat |
| `models/airguard_model.joblib` | Belum dibuat |

## 16. Alur kerja dan handoff modeling

```text
Dataset kualitas udara            [selesai]
        ↓
Pemeriksaan data                  [selesai]
        ↓
EDA                               [selesai]
        ↓
Preprocessing                     [selesai]
        ↓
Feature engineering               [selesai]
        ↓
Menentukan target klasifikasi     [selesai]
        ↓
Split data berbasis waktu         [selesai, sudah diperbaiki]
        ↓
Encoding target                   [selesai]
        ↓
Penanganan imbalance              [selesai]
        ↓
Training model                    [selesai]
        ↓
Evaluasi model                    [selesai]
        ↓
Pemilihan model terbaik           [selesai]
        ↓
Penyimpanan hasil untuk dashboard [belum]
```

### 16.1 Pembagian data yang digunakan

| Subset | Periode | Jumlah baris |
|---|---|---:|
| Train | 2022-08-18 sampai 2024-12-31 | 103.173 |
| Validation | 2025-01-01 sampai 2025-12-31 | 43.435 |
| Test | 2026-01-01 sampai 2026-10-21 | 34.986 |

### 16.2 Batasan untuk tahap berikutnya

- Jangan memakai random train-test split.
- Jangan menerapkan SMOTE pada validation atau test.
- Jangan memasukkan `target_pm2_5` atau `kategori_target_pm2_5` ke dalam fitur.
- Jangan memakai data test untuk tuning atau pemilihan model.
- Buat `X` dan `y` dari `df` yang sudah diurutkan. Jangan ubah urutan atau index `df` setelah itu.
- Laporkan macro F1 dan recall per kelas, bukan accuracy saja.
- Laporkan distribusi kelas per subset bersama hasil model.
