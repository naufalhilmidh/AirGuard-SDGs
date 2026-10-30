# Karakteristik Dataset: `airguard_harian_kualitas_udara_jawa.csv`
**Dokumen Referensi Resmi untuk Eksplorasi, Preprocessing, dan Modeling AI**  
*Proyek AirGuard SDGs (SDG 3: Good Health, SDG 11: Sustainable Cities, SDG 13: Climate Action)*

---

## 1. Ringkasan Eksekutif Dataset

Dataset `airguard_harian_kualitas_udara_jawa.csv` merupakan dataset panel time-series tingkat harian yang komprehensif, mencakup seluruh **119 Kabupaten dan Kota di 6 Provinsi se-Pulau Jawa** dalam kurun waktu lebih dari 4 tahun (Agustus 2022 hingga Oktober 2026). Dataset ini dirancang secara khusus untuk mendukung pengembangan model kecerdasan buatan (*Machine Learning* dan *Deep Learning*) dalam memprediksi konsentrasi partikulat halus (**PM2.5**) satu hari ke depan (*next-day forecasting*).

| Parameter | Nilai / Spesifikasi | Catatan Analisis |
| :--- | :--- | :--- |
| **Lokasi File** | `data/data_gabungan/airguard_harian_kualitas_udara_jawa.csv` | File gabungan primer regional Jawa |
| **Ukuran File Fisik** | ± 35.6 MB | Efisien untuk pemrosesan in-memory (Pandas / Polars) |
| **Dimensi Data** | **183.379 baris × 16 kolom** | $119 \text{ kab/kota} \times 1.541 \text{ hari}$ |
| **Kelengkapan Nilai (Nulls)** | **0 missing values (100% Complete)** | Tidak memerlukan imputasi nilai hilang global |
| **Rentang Waktu** | **04 Agustus 2022 s.d. 22 Oktober 2026** | **1.541 hari kalender berkelanjutan** |
| **Jeda Waktu (Gap)** | **0 hari (Tidak ada tanggal bolong)** | *Perfect balanced panel time-series* |
| **Cakupan Spasial** | **Pulau Jawa (6 Provinsi, 119 Kab/Kota)** | Banten, DKI, Jabar, Jateng, DIY, Jatim |
| **Tipe Masalah ML** | **Supervised Time-Series Regression Forecasting** | Target utama: $PM_{2.5(t+1)}$ |

---

## 2. Kamus Data & Spesifikasi Variabel

Dataset terdiri atas 16 fitur yang terbagi menjadi 3 kategori logis: **Metadata Geospasial & Demografis**, **Dimensi Temporal**, dan **Parameter Kualitas Udara (Polutan Dinamis)**.

| No | Nama Kolom | Tipe Data | Kategori Fitur | Satuan / Format | Rentang Nilai | Deskripsi & Peran untuk Modeling AI |
|:---|:---|:---|:---|:---|:---|:---|
| 1 | `kode_kabkota` | `float64` | Geospasial | Kode Wilayah Kemendagri | `31.01` – `36.74` | Identifier unik tingkat kabupaten/kota (misal: 31=DKI, 32=Jabar). |
| 2 | `nama_kabkota` | `object` | Geospasial | Teks Nama Resmi | 119 entitas | Nama kabupaten/kota, digunakan sebagai kunci pengelompokan (*grouping key*) untuk fitur lag/rolling. |
| 3 | `provinsi` | `object` | Geospasial | Teks Nama Provinsi | 6 entitas | Entitas hierarki wilayah tingkat 1; berguna untuk segmentasi model & analisis regional. |
| 4 | `tipe` | `object` | Demografis | Kategori (`Kabupaten` / `Kota`) | 2 kelas | Karakteristik urbanisasi (`Kabupaten`: 130.985 baris; `Kota`: 52.394 baris). |
| 5 | `latitude` | `float64` | Geospasial | Derajat Desimal | `-8.718` s.d. `-5.746` | Koordinat lintang pusat wilayah; fitur spasial untuk spatial embedding atau distance weighting. |
| 6 | `longitude` | `float64` | Geospasial | Derajat Desimal | `105.352` s.d. `114.366`| Koordinat bujur pusat wilayah; merepresentasikan gradien barat-ke-timur Pulau Jawa. |
| 7 | `elevasi_m` | `float64` | Geospasial | Meter di atas permukaan laut | `2.0` – `911.0` m | Ketinggian topografi; sangat berpengaruh pada inversi suhu dan dispersi polutan. |
| 8 | `luas_km2` | `float64` | Geospasial | Kilometer persegi ($km^2$) | `18.53` – `4.163.82` | Luas administratif wilayah; membedakan kota kompak padat vs kabupaten rural luas. |
| 9 | `penduduk` | `float64` | Demografis | Jiwa (Orang) | `29.742` – `5.809.790` | Proksi antropogenik (intensitas kendaraan, limbah domestik, dan aktivitas manusia). |
| 10 | `tanggal` | `object` | Temporal | Format `YYYY-MM-DD` | `2022-08-04` – `2026-10-22` | Sumbu waktu utama (*time index*); wajib dikonversi menjadi `datetime64[ns]`. |
| 11 | `pm10` | `float64` | Polutan | $\mu g/m^3$ (Konsentrasi harian) | `0.89` – `196.95` | Partikel kasar ($\le 10 \mu m$); korelasi sangat kuat dengan target ($r = 0.944$). |
| 12 | `pm2_5` | `float64` | **Target Utama** | $\mu g/m^3$ (Konsentrasi harian) | `0.62` – `159.68` | **Partikel halus ($\le 2.5 \mu m$) hari ke-$t$**. Dasar pembentukan target $t+1$. |
| 13 | `carbon_monoxide` | `float64` | Polutan | $\mu g/m^3$ (Konsentrasi harian) | `59.13` – `6.181.04` | Karbon monoksida ($CO$); proksi emisi gas buang kendaraan bermotor dan pembakaran. |
| 14 | `nitrogen_dioxide`| `float64` | Polutan | $\mu g/m^3$ (Konsentrasi harian) | `0.00` – `159.01` | Nitrogen dioksida ($NO_2$); indikator aktivitas lalu lintas tinggi dan industri fosil. |
| 15 | `sulphur_dioxide` | `float64` | Polutan | $\mu g/m^3$ (Konsentrasi harian) | `0.00` – `162.50` | Sulfur dioksida ($SO_2$); indikator emisi pembangkit listrik batu bara, industri, dan vulkanik. |
| 16 | `ozone` | `float64` | Polutan | $\mu g/m^3$ (Konsentrasi harian) | `8.96` – `228.58` | Ozon permukaan tanah ($O_3$); polutan sekunder hasil reaksi fotokimia sinar matahari. |

---

## 3. Statistik Deskriptif & Karakteristik Distribusi

Berikut adalah ringkasan parameter statistik matematis dari seluruh polutan dalam dataset ($N = 183.379$ baris):

| Polutan | Mean | Std Dev | Min | Q1 (25%) | Median (50%) | Q3 (75%) | Max | Skewness | Interpretasi Distribusi |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| **$PM_{2.5}$** | **37.04** | **22.62** | **0.62** | **19.31** | **31.72** | **49.40** | **159.68** | **+1.06** | *Moderately right-skewed*, rata-rata melebihi baku mutu WHO ($15\,\mu g/m^3$). |
| **$PM_{10}$** | 44.83 | 24.69 | 0.89 | 25.84 | 39.36 | 58.41 | 196.95 | +1.10 | Mengikuti pola yang identik dengan $PM_{2.5}$. |
| **$CO$** | 680.73 | 571.99 | 59.13 | 338.08 | 508.79 | 786.04 | 6181.04 | **+2.77** | *Highly skewed*, terdapat *extreme episodic spikes* (peristiwa polusi parah). |
| **$NO_2$** | 19.92 | 18.40 | 0.00 | 7.82 | 14.11 | 24.96 | 159.01 | **+2.22** | *Highly skewed*, konsentrasi terkonsentrasi di koridor kota besar & pantura. |
| **$SO_2$** | 13.95 | 14.36 | 0.00 | 3.69 | 9.08 | 19.28 | 162.50 | **+1.79** | Variasi lebar antara pesisir industri dengan pedesaan pegunungan. |
| **$O_3$** | 66.39 | 27.58 | 8.96 | 46.25 | 62.25 | 82.67 | 228.58 | +0.81 | Distribusi relatif simetris (*near-normal*), dipengaruhi radiasi UV harian. |

### Karakteristik Demografis & Topografi Wilayah
- **Elevasi (`elevasi_m`)**: Rentang 2 m (kota pantai seperti Surabaya, Jakarta Utara, Semarang) hingga 911 m (daerah pegunungan tinggi seperti Wonosobo, Magelang). Rata-rata 147.97 m.
- **Jumlah Penduduk (`penduduk`)**: Minimum 29.742 jiwa (Kepulauan Seribu) hingga 5.809.790 jiwa (Kabupaten Bogor).
- **Luas Wilayah (`luas_km2`)**: Minimum 18.53 $km^2$ (Kota Magelang / Kota Cirebon) hingga 4.163.82 $km^2$ (Kabupaten Sukabumi / Banyuwangi).

---

## 4. Karakteristik Temporal & Time-Series AI

### A. Autokorelasi & Dependensi Waktu (Lag Dynamics)
Analisis fungsi autokorelasi (ACF) untuk variabel target $PM_{2.5}$ yang dihitung per kabupaten/kota menunjukkan sifat autoregresif yang sangat kuat:

$$\text{Autokorelasi Rata-rata}: \quad \text{Lag-1} = 0.795 \quad\Big|\quad \text{Lag-2} = 0.656 \quad\Big|\quad \text{Lag-3} = 0.585 \quad\Big|\quad \text{Lag-7} = 0.514$$

> **Implikasi Modeling:**  
> Nilai autokorelasi Lag-1 sebesar **0.795** membuktikan bahwa kondisi polusi hari ini memiliki *memory retention* yang sangat dominan terhadap kondisi hari berikutnya. Fitur lag ($PM_{2.5(t)}$, $PM_{2.5(t-1)}$, $PM_{2.5(t-2)}$) dan moving averages (3-hari, 7-hari) akan menjadi prediktor paling signifikan dalam model ML.

### B. Pola Musiman (Seasonality Pulau Jawa)
Konsentrasi $PM_{2.5}$ harian berfluktuasi secara konsisten mengikuti pola musiman monsun di Pulau Jawa:
- **Puncak Polusi (Mei – Juli / Musim Kemarau)**: Rata-rata mencapai **42.04 $\mu g/m^3$** (Juni). Kurangnya curah hujan dan stabilitas atmosferik menahan partikulat polusi di dekat permukaan tanah (*trapped aerosol*).
- **Penurunan Polusi (Januari – Februari / Musim Hujan)**: Rata-rata turun menjadi **32.61 – 33.73 $\mu g/m^3$** akibat efek *wet scavenging* (pencucian aerosol oleh air hujan).

```
Rata-rata PM2.5 Bulanan (µg/m³):
Jan [█████████████] 32.61
Feb [█████████████] 33.73
Mar [██████████████] 36.82
Apr [██████████████] 37.05
Mei [███████████████] 39.03
Jun [████████████████] 42.04  <-- Puncak Polusi Tahunan
Jul [██████████████] 37.21
Agu [██████████████] 36.02
Sep [██████████████] 36.00
Okt [███████████████] 37.72
Nov [███████████████] 39.69  <-- Puncak Transisi
Des [██████████████] 36.85
```

### C. Skema Pembagian Data Waktu (Strict Temporal Split)
Mengacu pada standar time-series modeling pada proyek AirGuard, **dilarang keras menggunakan *random train-test split*** karena akan memicu kebocoran data (*lookahead bias*). Pembagian data dilakukan secara kronologis:

| Subset | Periode Kalender | Durasi | Jumlah Baris | Proporsi | Peran Modeling |
|:---|:---|:---:|---:|:---:|:---|
| **Training Set** | 04 Agustus 2022 s.d. 31 Desember 2024 | 881 hari | **104.839 baris** | 57.17% | Fitting bobot/parameter model ML |
| **Validation Set** | 01 Januari 2025 s.d. 31 Desember 2025 | 365 hari | **43.435 baris** | 23.69% | Hyperparameter tuning & early stopping |
| **Test Set (Holdout)** | 01 Januari 2026 s.d. 22 Oktober 2026 | 295 hari | **35.105 baris** | 19.14% | Evaluasi performa final (*out-of-sample*) |

---

## 5. Karakteristik Geospasial & Klaster Wilayah

### A. Pola Spasial per Provinsi
Kondisi kualitas udara di Pulau Jawa menunjukkan disparitas geografis yang nyata:

| Provinsi | Jumlah Kab/Kota | Total Baris | Rata-rata $PM_{2.5}$ | Median $PM_{2.5}$ | Max $PM_{2.5}$ | Karakteristik Utama |
|:---|:---:|---:|---:|---:|---:|:---|
| **DKI Jakarta** | 6 | 9.246 | **50.54 $\mu g/m^3$** | 49.28 | 150.09 | Wilayah metropolitan terpadat, emisi transportasi intensif. |
| **Banten** | 8 | 12.328 | **46.12 $\mu g/m^3$** | 44.38 | 154.93 | Koridor industri barat (Cilegon, Tangerang Raya). |
| **Jawa Barat** | 27 | 41.607 | **45.14 $\mu g/m^3$** | 41.09 | 154.62 | Pusat manufaktur nasional & aglomerasi Jabodetabek selatan. |
| **Jawa Tengah** | 35 | 53.935 | **34.79 $\mu g/m^3}$** | 30.04 | 143.03 | Jalur Pantura memiliki polusi tinggi, daerah pegunungan sedang. |
| **Jawa Timur** | 38 | 58.558 | **30.67 $\mu g/m^3$** | 26.33 | 159.68 | Polusi tinggi di Surabaya Raya, sangat bersih di ujung timur/Madura. |
| **DI Yogyakarta** | 5 | 7.705 | **26.78 $\mu g/m^3$** | 20.21 | 126.24 | Tingkat polusi terendah secara provinsi di Jawa. |

### B. Perbandingan Tipe Administratif (Kabupaten vs Kota)
- **Kota ($N = 34$ entitas, 52.394 baris)**: Memiliki rata-rata $PM_{2.5}$ sebesar **42.95 $\mu g/m^3$** dengan median 38.08 $\mu g/m^3$.
- **Kabupaten ($N = 85$ entitas, 130.985 baris)**: Memiliki rata-rata $PM_{2.5}$ sebesar **34.68 $\mu g/m^3$** dengan median 29.60 $\mu g/m^3$.
- Kota cenderung memiliki paparan polusi 23.8% lebih tinggi dibandingkan kabupaten.

### C. Ekstremitas Wilayah (Top vs Bottom)
- **5 Wilayah Paling Tercemar ($PM_{2.5}$ Rata-rata tertinggi ~67.20 $\mu g/m^3$)**:
  1. Kota Depok (Jawa Barat)
  2. Kota Tangerang Selatan (Banten)
  3. Kota Administrasi Jakarta Selatan (DKI Jakarta)
  4. Kota Administrasi Jakarta Timur (DKI Jakarta)
  5. Kota Bekasi (Jawa Barat)
- **5 Wilayah Paling Bersih ($PM_{2.5}$ Rata-rata terendah < 17 $\mu g/m^3$)**:
  1. Kabupaten Sumenep (Jatim) – $13.83\,\mu g/m^3$
  2. Kabupaten Kulon Progo (DIY) – $15.59\,\mu g/m^3$
  3. Kabupaten Situbondo (Jatim) – $16.05\,\mu g/m^3$
  4. Kabupaten Pamekasan (Jatim) – $16.48\,\mu g/m^3$
  5. Kabupaten Banyuwangi (Jatim) – $16.52\,\mu g/m^3$

> ⚠️ **Catatan Kritis Arsitektur Data Spasial (Grid Resolution Finding):**  
> Analisis data menunjukkan bahwa dari 119 entitas administratif, terdapat **63 deret waktu unik (*unique time-series profiles*)**. Hal ini terjadi karena data sumber atmosferik (Open-Meteo / ECMWF Reanalysis) memiliki resolusi grid spasial sekitar $0.1^\circ$ hingga $0.25^\circ$ (~11–28 km). Daerah berdekatan seperti Jakarta Selatan, Jakarta Timur, Depok, dan Bekasi jatuh pada *grid cell* yang identik sehingga nilai polutannya sama.  
> **Konsekuensi Modeling AI:** Hindari *spatial random cross-validation* antar kota bertetangga langsung karena dapat menimbulkan *spatial data leakage*. Gunakan *GroupKFold* berbasis koordinat cluster atau pertahankan pemisahan berbasis waktu (*Temporal Split*).

---

## 6. Analisis Multivariat & Hubungan Antar Fitur

### A. Matriks Korelasi terhadap Target $PM_{2.5}$
Berdasarkan uji korelasi linear Pearson ($r$):

| Fitur | Korelasi ($r$) terhadap $PM_{2.5}$ | Sifat Hubungan | Catatan Teknis untuk Model AI |
|:---|---:|:---|:---|
| `pm10` | **+0.9436** | Sangat Kuat Positif | Multikolinearitas ekstrim. Hindari memasukkan `pm10(t+1)` sebagai fitur. Jika digunakan, gunakan `pm10_lag1`. |
| `nitrogen_dioxide` | **+0.6911** | Kuat Positif | Sinyal kuat aktivitas pembakaran; sangat baik sebagai fitur eksogen. |
| `sulphur_dioxide` | **+0.5660** | Moderat Positif | Indikasi emisi industri; prediktor pelengkap yang baik. |
| `carbon_monoxide` | **+0.5447** | Moderat Positif | Menangkap polusi saat kemacetan atau kebakaran biomassa. |
| `ozone` | **+0.3401** | Lemah-Moderat Positif | Reaktif terhadap radiasi; berguna untuk interaksi musiman. |
| `penduduk` | **+0.2098** | Lemah Positif | Semakin padat penduduk, kecenderungan baseline polusi meningkat. |
| `luas_km2` | **-0.1149** | Lemah Negatif | Wilayah luas biasanya didominasi pedesaan dengan polusi lebih rendah. |
| `elevasi_m` | **+0.0211** | Sangat Lemah Linear | Hubungan non-linear (tergantung fenomena inversi suhu lembah vs puncak). |

---

## 7. Distribusi Kategori Risiko Kesehatan (SDGs 3 & 11)

Berdasarkan klasifikasi standar ambang batas harian (kombinasi KLHK ISPU & US-EPA AQI):

| Kategori Risiko | Rentang $PM_{2.5}$ ($\mu g/m^3$) | Frekuensi (Baris) | Persentase | Dampak Kesehatan & Storytelling SDGs |
|:---|:---:|---:|---:|:---|
| **Baik (*Good*)** | $0.0 - 15.5$ | 29.708 | **16.20%** | Tingkat kualitas udara ideal sesuai rekomendasi WHO. |
| **Sedang (*Moderate*)** | $15.6 - 55.4$ | 118.228 | **64.47%** | Mayoritas kondisi harian di Pulau Jawa; risiko ringan pada kelompok sensitif. |
| **Tidak Sehat (*Unhealthy*)** | $55.5 - 150.4$ | 35.431 | **19.32%** | Membahayakan kelompok rentan (lansia, anak, penderita asma/ISPA). |
| **Sangat Tidak Sehat (*Very Unhealthy*)** | $150.5 - 250.4$ | 12 | **0.007%** | Kejadian polusi ekstrim sporadis di kawasan industri padat. |
| **Berbahaya (*Hazardous*)** | $> 250.4$ | 0 | **0.00%** | Tidak terdeteksi dalam dataset harian ini. |

---

## 8. Panduan Teknis & Blueprint Modeling AI

### A. Definisi Target Prediksi
Model diarahkan untuk memprediksi nilai kontinu $PM_{2.5}$ satu hari ke depan untuk kota yang sama:

$$\text{Target}: \quad y_{i, t+1} = PM_{2.5(i, t+1)}$$

Untuk keperluan dashboard, nilai prediksi kontinu $\hat{y}_{i, t+1}$ kemudian dipetakan ke dalam kategori risiko (Baik, Sedang, Tidak Sehat, Sangat Tidak Sehat).

### B. Model Baseline Wajib
Sesuai pedoman proyek, model Machine Learning harus membuktikan keunggulannya dibandingkan dua model *baseline* sederhana:
1. **Persistence Baseline (Naïve Model)**:
   $$\hat{y}_{t+1} = y_t$$
   *(Memprediksi bahwa besok polusinya sama persis dengan hari ini).*
2. **Rolling Moving Average Baseline**:
   $$\hat{y}_{t+1} = \frac{1}{k} \sum_{j=0}^{k-1} y_{t-j} \quad (\text{untuk } k=3 \text{ dan } k=7)$$

### C. Strategi Feature Engineering yang Direkomendasikan
Sebelum data diumpankan ke model, lakukan rekayasa fitur dengan pengelompokan ketat per `kode_kabkota` atau `nama_kabkota`:

```python
# CONTOH KODE PREPROCESSING BEBAS LEAKAGE
df = df.sort_values(['nama_kabkota', 'tanggal'])

# 1. Target Next-Day
df['target_pm2_5'] = df.groupby('nama_kabkota')['pm2_5'].shift(-1)

# 2. Lag Features (Hanya menggunakan data historis t, t-1, t-2, dst.)
for lag in [1, 2, 3, 7]:
    df[f'pm2_5_lag_{lag}'] = df.groupby('nama_kabkota')['pm2_5'].shift(lag - 1)
    df[f'pm10_lag_{lag}'] = df.groupby('nama_kabkota')['pm10'].shift(lag - 1)
    df[f'no2_lag_{lag}'] = df.groupby('nama_kabkota')['nitrogen_dioxide'].shift(lag - 1)

# 3. Rolling Statistics (Historical Only)
df['pm2_5_roll_mean_3d'] = df.groupby('nama_kabkota')['pm2_5'].transform(
    lambda x: x.shift(0).rolling(window=3).mean()
)
df['pm2_5_roll_mean_7d'] = df.groupby('nama_kabkota')['pm2_5'].transform(
    lambda x: x.shift(0).rolling(window=7).mean()
)
df['pm2_5_roll_std_7d'] = df.groupby('nama_kabkota')['pm2_5'].transform(
    lambda x: x.shift(0).rolling(window=7).std()
)

# 4. Temporal Features
df['tanggal'] = pd.to_datetime(df['tanggal'])
df['bulan'] = df['tanggal'].dt.month
df['hari_dalam_minggu'] = df['tanggal'].dt.dayofweek
df['hari_dalam_tahun'] = df['tanggal'].dt.dayofyear

# Cyclical Encoding untuk menangkap periodisitas tahunan
df['sin_bulan'] = np.sin(2 * np.pi * df['bulan'] / 12)
df['cos_bulan'] = np.cos(2 * np.pi * df['bulan'] / 12)
```

### D. Pencegahan Data Leakage (Golden Rules)
1. **Dilarang Menghitung Rolling/Lag secara Global**: Selalu terapkan fungsi `.groupby('nama_kabkota')`. Mengabaikan *grouping* akan menyebabkan data hari pertama di Kabupaten Bandung terisi data hari terakhir dari Kabupaten Bogor!
2. **Dilarang Menggunakan Polutan Masa Depan**: Jika model memprediksi $PM_{2.5}$ hari esok ($t+1$), semua fitur polutan lain ($CO, NO_2, SO_2, O_3$) yang digunakan harus berasal dari waktu $t$ atau sebelumnya.
3. **Pembersihan Baris Akibat Lag & Target Shift**: Baris pertama per kota (yang menghasilkan `NaN` pada fitur lag) dan baris terakhir per kota (22 Oktober 2026 yang menghasilkan `NaN` pada target $t+1$) harus di-drop sebelum pelatihan model.

### E. Algoritma Model yang Direkomendasikan
1. **LightGBM Regressor / XGBoost Regressor (Primary Choice)**:
   - Sangat cepat memproses 180k+ baris.
   - Mampu menangani fitur tabular campuran (kategorikal provinsi/tipe, kontinu koordinat, lag polutan).
   - Mampu menangani non-linearitas dan korelasi musiman.
2. **CatBoost Regressor**:
   - Optimal jika fitur kategorikal wilayah (`nama_kabkota`, `provinsi`, `tipe`) disertakan langsung tanpa one-hot encoding.
3. **Random Forest / Ridge Regression**:
   - Sebagai pembanding perantara antara *baseline* dan *gradient boosted trees*.

### F. Metrik Evaluasi Kinerja
Setiap model wajib dievaluasi menggunakan metrik berikut pada **Test Set (Tahun 2026)**:
- **MAE (*Mean Absolute Error*)**: Metrik primer interpretatif ($\mu g/m^3$).
- **RMSE (*Root Mean Squared Error*)**: Memberikan penalti lebih berat pada kesalahan prediksi ekstrim.
- **$R^2$ (*Coefficient of Determination*)**: Menilai proporsi variansi yang dapat dijelaskan oleh model ($R^2 > 0.65$ diharapkan).
- **Classification Accuracy / Macro F1-Score**: Dihitung setelah nilai prediksi kontinu dipetakan kembali ke 4 kategori risiko dashboard.

---

## 9. Kesimpulan & Rekomendasi Alur Kerja AI

1. **Dataset Bersih & Siap Pakai**: Dataset ini memiliki kualitas struktural yang tinggi (0 missing values, sekuens kalender penuh).
2. **Sinyal Prediktif Sangat Kuat**: Dependensi autoregresif ($r = 0.795$) dan korelasi polutan precursor ($NO_2, SO_2$) menyediakan sinyal yang kaya untuk model prediktif.
3. **Langkah Kerja Berikutnya**:
   - Jalankan notebook `03_preprocessing` untuk menghasilkan file terstandarisasi dengan fitur lag & rolling (`data/data_gabungan/airguard_jawa_preprocessed.csv`).
   - Lakukan training baseline model (Persistence & Rolling 3-hari) pada notebook `04_modeling`.
   - Lakukan hyperparameter tuning LightGBM / XGBoost dengan data train 2022-2024 dan validation 2025.
   - Simpan model terbaik ke dalam direktori `models/` beserta file metrik evaluasi `model_metrics.csv` untuk disajikan pada dashboard interaktif.
