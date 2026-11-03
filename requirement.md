# AirGuard SDGs: Requirement, EDA, dan Rencana Implementasi

## 1. Tujuan proyek

AirGuard adalah sistem pemantauan dan prediksi kualitas udara untuk kabupaten/kota di Pulau Jawa. Fokus utama sistem adalah memprediksi konsentrasi PM2.5 pada hari berikutnya (*next-day forecasting*) dan menerjemahkan hasilnya menjadi informasi risiko yang mudah dipahami melalui dashboard.

Keterkaitan SDGs:

- SDG 3: Good Health and Well-being
- SDG 11: Sustainable Cities and Communities
- SDG 13: Climate Action

Target pemodelan utama:

`target_pm2_5 = PM2.5 pada hari berikutnya untuk kabupaten/kota yang sama`

Proyek ini merupakan masalah regresi deret waktu. Kategori risiko pada dashboard adalah lapisan interpretasi hasil prediksi, bukan target utama model.

## 2. Sumber dan struktur data

### Sumber data

Data kualitas udara diperoleh dari Open-Meteo Air Quality API. Data tersebut merupakan estimasi model atmosfer berbasis koordinat, bukan pembacaan langsung dari sensor pemantauan pada setiap kabupaten/kota.

### Cakupan data terakhir

- Wilayah: 119 kabupaten/kota di Pulau Jawa
- Periode: 4 Agustus 2022 sampai 22 Oktober 2026
- Jumlah baris: 183.379
- Jumlah hari per wilayah: 1.541 hari
- Nilai kosong pada data gabungan: 0
- Duplikasi tanggal dalam satu wilayah: 0

### Atribut utama

| Kelompok | Atribut |
|---|---|
| Identitas wilayah | `kode_kabkota`, `nama_kabkota`, `provinsi`, `tipe` |
| Geografis | `latitude`, `longitude`, `elevasi_m`, `luas_km2`, `penduduk` |
| Waktu | `tanggal` |
| Polutan | `pm2_5`, `pm10`, `carbon_monoxide`, `nitrogen_dioxide`, `sulphur_dioxide`, `ozone` |

Catatan: beberapa kabupaten/kota dapat menerima nilai yang sama karena koordinatnya dipetakan ke grid atmosfer Open-Meteo yang sama. Dari pemeriksaan sebelumnya, 119 wilayah merepresentasikan sekitar 111 titik grid unik. Hal ini perlu dijelaskan pada dashboard agar nilai yang identik tidak dianggap sebagai kesalahan data.

## 3. Hasil EDA sementara

### 3.1 Kelengkapan dan konsistensi

Pemeriksaan awal menunjukkan bahwa:

- Seluruh 119 kabupaten/kota memiliki data.
- Setiap kabupaten/kota memiliki jumlah hari yang sama.
- Tidak terdapat missing value pada atribut utama.
- Tidak terdapat duplikasi kombinasi wilayah dan tanggal.
- Tidak ada masalah tanggal yang hilang pada data akhir yang digunakan.

Dengan demikian, data dapat dilanjutkan ke feature engineering tanpa imputasi missing value. Pemeriksaan ini tetap perlu dijalankan ulang setelah setiap proses penggabungan atau transformasi.

### 3.2 Distribusi variabel

Seluruh variabel polutan cenderung menceng ke kanan, sehingga distribusinya tidak normal secara visual:

| Variabel | Skewness |
|---|---:|
| `carbon_monoxide` | 2,765 |
| `nitrogen_dioxide` | 2,221 |
| `sulphur_dioxide` | 1,791 |
| `pm10` | 1,103 |
| `pm2_5` | 1,063 |
| `ozone` | 0,810 |

Interpretasi:

- Sebagian besar hari berada pada konsentrasi rendah sampai menengah.
- Terdapat ekor panjang yang menunjukkan episode polusi tinggi.
- Nilai ekstrem tidak langsung dihapus karena dapat merupakan kejadian polusi yang penting bagi sistem peringatan dini.
- Model berbasis pohon tidak mensyaratkan distribusi normal. Transformasi log hanya akan dipertimbangkan jika dibutuhkan oleh model tertentu.

### 3.3 Korelasi terhadap target

Korelasi Pearson terhadap target PM2.5 hari berikutnya menunjukkan:

| Variabel | Korelasi | Interpretasi |
|---|---:|---|
| `pm2_5` | 0,876 | Sangat kuat, positif |
| `pm2_5_rolling_3` | 0,843 | Sangat kuat, positif |
| `pm2_5_rolling_7` | 0,823 | Sangat kuat, positif |
| `pm2_5_rolling_14` | 0,814 | Sangat kuat, positif |
| `pm10` | 0,801 | Sangat kuat, positif |
| `pm2_5_lag_1` | 0,784 | Kuat, positif |
| `pm2_5_lag_2` | 0,736 | Kuat, positif |
| `pm2_5_lag_3` | 0,711 | Kuat, positif |
| `pm2_5_lag_7` | 0,688 | Kuat, positif |
| `nitrogen_dioxide` | 0,680 | Kuat, positif |
| `carbon_monoxide` | 0,604 | Kuat, positif |
| `sulphur_dioxide` | 0,543 | Sedang, positif |
| `ozone` | 0,139 | Lemah |
| `wind_speed_10m` | -0,462 | Sedang-kuat, negatif |
| `surface_pressure` | -0,199 | Lemah |
| Variabel cuaca lain | sekitar -0,07 sampai -0,02 | Lemah |

Temuan penting:

- Nilai PM2.5 sebelumnya, rolling average, dan PM10 menjadi kandidat fitur utama.
- Korelasi tinggi PM2.5 dan PM10 perlu diperhatikan karena dapat menimbulkan redundansi fitur.
- Korelasi tidak membuktikan hubungan sebab-akibat.
- Korelasi fitur harus dihitung menggunakan data yang tersedia sebelum waktu prediksi agar tidak terjadi kebocoran data.

Catatan: korelasi cuaca di atas berasal dari analisis sebelumnya. Dataset kualitas udara terbaru hanya berisi atribut polutan, sehingga fitur cuaca belum tersedia pada dataset final saat ini.

### 3.4 Tren dan musiman

EDA menunjukkan adanya variasi bulanan yang kuat. Salah satu perubahan paling terlihat terjadi sekitar Oktober-November 2024:

- Rata-rata PM2.5 global sekitar Oktober 2024: 27,95 µg/m³
- Rata-rata PM2.5 global sekitar November 2024: 51,71 µg/m³
- Kenaikan rata-rata: sekitar 23,76 µg/m³

Beberapa wilayah dengan kenaikan Oktober-November terbesar antara lain:

- Kabupaten Semarang
- Kota Salatiga
- Kabupaten Nganjuk
- Kabupaten Ngawi
- Kota Madiun
- Kabupaten Madiun
- Kabupaten Grobogan

Perubahan tersebut perlu dianalisis sebagai episode polusi atau perubahan pola musiman. Model tidak boleh menghapus periode ini secara otomatis karena episode tersebut justru relevan untuk sistem peringatan dini.

## 4. Preprocessing

Output preprocessing yang direncanakan:

`data/data_gabungan/airguard_preprocessed.csv`

Tahapan:

1. Membaca data gabungan.
2. Mengubah `tanggal` menjadi tipe datetime.
3. Mengurutkan data berdasarkan `nama_kabkota` dan `tanggal`.
4. Memastikan satu baris merepresentasikan satu wilayah pada satu tanggal.
5. Memeriksa kembali missing value, duplikasi, dan rentang tanggal.
6. Menghitung feature engineering secara terpisah untuk setiap kabupaten/kota.
7. Membuat target hari berikutnya.
8. Menghapus baris yang memang tidak dapat digunakan karena belum memiliki histori lengkap atau target berikutnya.

### 4.1 Feature engineering

#### Fitur lag PM2.5

Fitur lag menyimpan nilai PM2.5 pada hari sebelumnya:

- `pm2_5_lag_1`
- `pm2_5_lag_2`
- `pm2_5_lag_3`
- `pm2_5_lag_7`
- `pm2_5_lag_14`

Lag wajib dihitung per kabupaten/kota, bukan pada seluruh dataframe sekaligus, agar data antarwilayah tidak tercampur.

#### Fitur rolling PM2.5

Rolling average merangkum rata-rata PM2.5 beberapa hari terakhir:

- `pm2_5_rolling_3`
- `pm2_5_rolling_7`
- `pm2_5_rolling_14`

Rolling harus menggunakan nilai historis saja. Nilai hari yang sedang diprediksi dan nilai masa depan tidak boleh masuk ke dalam perhitungan.

Perbedaan lag dan rolling:

- Lag adalah nilai PM2.5 pada satu titik waktu tertentu.
- Rolling adalah ringkasan rata-rata dari beberapa hari terakhir.

#### Fitur kalender

Fitur waktu yang akan dicoba:

- tahun
- bulan
- hari dalam minggu
- hari dalam tahun
- akhir pekan
- sin/cos bulan untuk menangkap pola siklus tahunan

#### Target

Target dibuat dengan menggeser PM2.5 satu hari ke depan dalam setiap kabupaten/kota:

`target_pm2_5 = pm2_5.shift(-1)`

Baris terakhir pada setiap kabupaten/kota akan kehilangan target dan harus dikeluarkan dari data pelatihan.

#### Pencegahan data leakage

- Tidak menggunakan nilai masa depan untuk membuat fitur.
- Tidak menggunakan `target_pm2_5` sebagai fitur.
- Tidak menggunakan US AQI sebagai fitur karena terlalu dekat dengan PM2.5 dan berisiko menyebabkan leakage.
- Scaler atau encoder, jika diperlukan, hanya di-fit pada data training.
- Fitur lag dan rolling selalu dihitung per kabupaten/kota.

## 5. Definisi kategori risiko

Kategori operasional untuk keperluan dashboard:

| Rentang PM2.5 | Label |
|---:|---|
| ≤ 15 µg/m³ | Baik (Aman) |
| > 15 sampai 55 µg/m³ | Sedang (Waspada) |
| > 55 µg/m³ | Tidak Sehat (Bahaya) |

Ambang ini harus ditampilkan sebagai definisi operasional proyek, bukan klaim diagnosis medis. Dashboard harus mencantumkan sumber atau justifikasi ambang yang dipakai pada dokumentasi final.

## 6. Rencana pemodelan

### 6.1 Jenis masalah

Pemodelan utama adalah regresi forecasting:

> memprediksi nilai PM2.5 pada hari berikutnya untuk setiap kabupaten/kota.

Klasifikasi risiko hanya digunakan sebagai lapisan interpretasi:

1. model menghasilkan prediksi numerik PM2.5;
2. prediksi tersebut dipetakan ke kategori risiko;
3. kategori ditampilkan pada peta dan tabel dashboard.

### 6.2 Model yang akan dibandingkan

Tiga model machine learning yang akan dicoba:

1. **LightGBM Regressor**
   - Kandidat model utama.
   - Efisien untuk data tabular berukuran besar.
   - Dapat menangkap hubungan non-linear dan interaksi antarfitur.
   - Menyediakan feature importance.

2. **Extra Trees Regressor**
   - Model ensemble berbasis banyak pohon acak.
   - Cocok sebagai pembanding non-linear yang kuat.
   - Relatif tahan terhadap skala fitur dan outlier.

3. **HistGradientBoosting Regressor**
   - Model boosting berbasis histogram.
   - Efisien untuk data tabular besar.
   - Menjadi pembanding alternatif yang tidak bergantung pada library LightGBM.

Selain ketiga model tersebut, wajib digunakan baseline:

- Persistence baseline: prediksi besok = PM2.5 hari ini.
- Rolling baseline: prediksi besok = rata-rata PM2.5 beberapa hari terakhir.

Model machine learning harus dibandingkan dengan baseline. Model terbaik bukan hanya yang memiliki skor bagus, tetapi yang benar-benar mengungguli baseline pada data uji.

### 6.3 Pembagian data berbasis waktu

Random train-test split tidak digunakan.

Rencana split:

- Training: 2022-08 sampai 2024-12
- Validasi: 2025
- Pengujian akhir: 2026

Semua wilayah tetap dipertahankan pada setiap periode bila tersedia. Evaluasi akhir dilakukan pada periode yang tidak pernah digunakan untuk melatih atau memilih model.

### 6.4 Metrik evaluasi

Metrik yang dicatat:

- MAE: rata-rata kesalahan absolut, mudah dibaca dalam satuan µg/m³.
- RMSE: memberi penalti lebih besar pada kesalahan besar.
- R²: proporsi variasi target yang dapat dijelaskan model.

Output pemodelan:

- `data/data_gabungan/airguard_predictions.csv`
- `data/data_gabungan/model_metrics.csv`
- `data/data_gabungan/feature_importance.csv`
- model dan pipeline tersimpan di folder `models/`

Kolom prediksi minimum:

- `nama_kabkota`
- `provinsi`
- `tanggal`
- `actual_pm2_5`
- `predicted_pm2_5`
- `risk_category`
- `model_name`

### 6.5 Clustering wilayah

Clustering digunakan sebagai analisis segmentasi wilayah, bukan sebagai pengganti forecasting. Tujuannya adalah mengelompokkan kabupaten/kota yang memiliki karakteristik kualitas udara serupa sehingga dashboard dapat menunjukkan zona prioritas pemantauan.

Unit analisis clustering adalah satu kabupaten/kota. Data harian diringkas menjadi satu baris per wilayah dengan variabel berikut:

| Variabel clustering | Fungsi |
|---|---|
| `rata_rata_pm25` | Tingkat polusi rata-rata |
| `median_pm25` | Kondisi tengah yang lebih tahan terhadap outlier |
| `maksimum_pm25` | Nilai PM2.5 tertinggi |
| `persentase_hari_tinggi` | Frekuensi hari PM2.5 di atas 55 µg/m³ |
| `jumlah_episode` | Banyaknya episode polusi |
| `durasi_episode_terpanjang` | Durasi episode polusi terburuk |
| `standar_deviasi_pm25` | Tingkat variabilitas kualitas udara |
| `rata_rata_pm10` | Profil partikulat berukuran lebih besar |
| `rata_rata_nitrogen_dioxide` | Profil polutan terkait aktivitas perkotaan |
| `rata_rata_carbon_monoxide` | Profil tambahan polusi wilayah |

Kolom identitas seperti `nama_kabkota`, `provinsi`, dan `kode_kabkota` tidak digunakan sebagai fitur numerik clustering. Kolom tersebut digunakan kembali sebagai label hasil.

Metode yang akan dicoba:

1. Standardisasi fitur dengan `StandardScaler`.
2. K-Means sebagai metode utama karena mudah dijelaskan dan divisualisasikan.
3. Pengujian beberapa nilai jumlah cluster, misalnya `k = 2` sampai `k = 6`.
4. Pemilihan jumlah cluster menggunakan Silhouette Score, Elbow Method, dan interpretasi substantif.
5. Pembuatan profil setiap cluster berdasarkan nilai rata-rata fitur.

Output clustering:

- `data/data_gabungan/clustering_wilayah.csv`
- kolom `nama_kabkota`, `provinsi`, `cluster`, dan fitur ringkasan
- model dan scaler clustering di folder `models/`

Cluster diberi nama berdasarkan karakteristik data, misalnya risiko relatif rendah dan stabil, risiko sedang atau musiman, serta risiko tinggi dan persisten. Nama cluster tidak ditentukan hanya dari warna peta.

### 6.6 Klasifikasi kategori risiko

Klasifikasi digunakan sebagai lapisan interpretasi dari nilai PM2.5, baik nilai aktual maupun hasil prediksi. Model utama tetap berupa regresi forecasting karena targetnya adalah angka PM2.5.

Alurnya adalah:

1. Model regresi menghasilkan `predicted_pm2_5`.
2. Nilai prediksi dipetakan ke ambang risiko.
3. Hasilnya disimpan sebagai `risk_category`.

| Nilai PM2.5 | Kategori |
|---:|---|
| ≤ 15 µg/m³ | Baik (Aman) |
| > 15 sampai 55 µg/m³ | Sedang (Waspada) |
| > 55 µg/m³ | Tidak Sehat (Bahaya) |

Klasifikasi risiko digunakan untuk peta dan tabel dashboard, bukan sebagai target utama model terpisah. Model klasifikasi terpisah hanya dipertimbangkan jika evaluasi berbasis kelas diperlukan.

## 7. Requirement dashboard awal

Catatan: rancangan dashboard inti yang berlaku untuk implementasi terbaru dijelaskan pada Bagian 10. Tab cuaca tetap opsional sampai data cuaca berhasil digabungkan.

### Tab 1 — Ringkasan

1. Pilihan tampilan berdasarkan kabupaten/kota atau provinsi.
2. Empat kartu angka:
   - PM2.5 hari ini tertinggi.
   - Prediksi PM2.5 besok tertinggi.
   - Jumlah daerah berisiko tinggi besok.
   - Jumlah wilayah yang dipantau.
3. Peta risiko besok dengan warna sesuai kategori dan legenda warna.
4. Tabel peringkat daerah yang dapat diurutkan dan dicari.
5. Informasi tanggal pembaruan data dan tanggal prediksi harus terlihat.

### Tab 2 — Tren & Prediksi

1. Grafik PM2.5 aktual dibandingkan prediksi model.
2. Garis rata-rata bergerak 7 hari.
3. Garis ambang polusi tinggi.
4. Grafik selisih prediksi dan kenyataan:
   `error = aktual - prediksi`.
5. Tabel episode polusi tinggi, yaitu periode beberapa hari berturut-turut di atas ambang yang dipilih.
6. Pilihan tampilan per kabupaten/kota atau per provinsi.
7. Informasi jumlah hari dan rentang tanggal pada grafik.

### Tab 3 — Cuaca

1. Heatmap korelasi PM2.5 dengan:
   - suhu
   - kelembapan
   - hujan
   - angin
   - tekanan udara
   - tutupan awan
2. Grafik sebar PM2.5 terhadap satu variabel cuaca yang dipilih.
3. Rata-rata PM2.5 per bulan untuk melihat pola musiman.
4. Keterangan sumber data cuaca, periode, dan satuan.

Status data: fitur cuaca perlu dikumpulkan atau digabungkan dari sumber cuaca terpisah karena dataset kualitas udara terbaru hanya berisi polutan. Jika data cuaca tidak tersedia pada versi final, Tab 3 dapat sementara menampilkan hubungan PM2.5 dengan polutan lain dan diberi label sebagai alternatif analisis.

### Tab 4 — Model

1. Penjelasan istilah:
   - baseline
   - MAE
   - RMSE
   - R²
2. Tabel perbandingan model.
3. Grafik perbandingan MAE.
4. Feature importance dari model terbaik.
5. Grafik aktual dibandingkan prediksi.
6. Keterangan periode training, validasi, dan pengujian.
7. Keterangan bahwa prediksi adalah estimasi model dan bukan pengukuran sensor langsung.

## 8. Validasi dan kriteria selesai

Sebelum modeling dianggap selesai:

- [ ] Tidak ada missing pada target.
- [ ] Tidak ada duplikasi wilayah-tanggal.
- [ ] Lag dan rolling dihitung per kabupaten/kota.
- [ ] Tidak ada fitur yang memakai data masa depan.
- [ ] Split data menggunakan urutan waktu.
- [ ] Persistence dan rolling baseline tersedia.
- [ ] LightGBM, Extra Trees, dan HistGradientBoosting dibandingkan.
- [ ] MAE, RMSE, dan R² dicatat untuk validasi dan test.
- [ ] Prediksi disimpan bersama tanggal dan wilayah.
- [ ] Feature importance disimpan.
- [ ] Model terbaik dan pipeline preprocessing disimpan.
- [ ] Dashboard membaca file output model yang sama dengan yang digunakan saat evaluasi.
- [ ] Kategori risiko dan ambangnya terdokumentasi.
- [ ] Sumber data, keterbatasan grid, dan periode data dijelaskan pada dashboard.

## 9. Keterbatasan yang harus disampaikan

- Data Open-Meteo berbasis estimasi model atmosfer dan grid, bukan sensor langsung pada setiap wilayah.
- Satu titik grid dapat digunakan oleh beberapa kabupaten/kota.
- Korelasi tidak dapat dianggap sebagai hubungan sebab-akibat.
- Dataset saat ini belum menyertakan cuaca sehingga analisis Tab 3 memerlukan sumber tambahan.
- Ambang risiko merupakan kategori operasional untuk dashboard.
- Prediksi tidak boleh diposisikan sebagai diagnosis medis.
- Perubahan besar pada November 2024 perlu dievaluasi sebagai episode polusi atau perubahan distribusi data.

## 10. Dashboard inti versi revisi

Dashboard memiliki dua keluaran analitik utama:

1. **Segmentasi wilayah**: peta Pulau Jawa dengan tiga warna cluster berdasarkan karakteristik kualitas udara.
2. **Prediksi deret waktu**: line chart PM2.5 aktual dibandingkan prediksi model untuk wilayah yang dipilih.

### 10.1 Peta segmentasi wilayah

Peta menampilkan satu warna untuk setiap cluster. Warna hanya berfungsi sebagai pembeda visual; makna cluster ditentukan dari profil statistiknya.

Informasi yang ditampilkan pada tooltip:

- nama kabupaten/kota
- provinsi
- cluster
- rata-rata PM2.5
- persentase hari di atas ambang risiko
- durasi episode polusi terpanjang

Legenda peta harus menjelaskan nama cluster, contohnya:

- hijau: risiko relatif rendah dan stabil
- kuning: risiko sedang atau musiman
- merah: risiko tinggi dan persisten

### 10.2 Peta prediksi risiko

Peta prediksi merupakan mode tampilan yang berbeda dari peta cluster. Peta ini menggunakan hasil `predicted_pm2_5` untuk hari berikutnya.

Legenda kategori risiko:

- hijau: Baik (Aman)
- kuning: Sedang (Waspada)
- merah: Tidak Sehat (Bahaya)

Legenda cluster dan legenda risiko tidak boleh digabung karena keduanya memiliki arti yang berbeda.

### 10.3 Line chart aktual dan prediksi

Line chart menampilkan:

- garis PM2.5 aktual
- garis PM2.5 prediksi model
- garis rata-rata bergerak 7 hari
- garis ambang polusi tinggi pada 55 µg/m³

Sumbu X adalah tanggal dan sumbu Y adalah PM2.5 dalam µg/m³. Grafik dapat difilter berdasarkan kabupaten/kota, provinsi, cluster, model, dan rentang tanggal.

Tambahan informasi pada grafik:

- nilai prediksi hari berikutnya
- tanggal pembaruan data
- MAE pada wilayah atau periode yang sedang dipilih
- selisih aktual dan prediksi

### 10.4 Struktur dashboard inti

#### Tab 1: Ringkasan

- kartu PM2.5 tertinggi hari ini
- kartu prediksi PM2.5 tertinggi besok
- kartu jumlah wilayah berisiko tinggi besok
- kartu jumlah wilayah yang dipantau
- pilihan tampilan kabupaten/kota atau provinsi
- toggle peta cluster dan peta prediksi risiko
- tabel ranking yang dapat dicari dan diurutkan

#### Tab 2: Tren dan Prediksi

- line chart aktual versus prediksi
- rolling average 7 hari
- ambang polusi tinggi
- grafik error prediksi
- tabel episode polusi tinggi
- filter wilayah, provinsi, cluster, model, dan tanggal

#### Tab 3: Profil Cluster

- peta tiga warna cluster
- jumlah wilayah pada setiap cluster
- karakteristik rata-rata setiap cluster
- tabel anggota cluster
- radar chart atau bar chart profil fitur cluster

#### Tab 4: Evaluasi Model

- penjelasan baseline, MAE, RMSE, dan R²
- tabel perbandingan model
- grafik perbandingan MAE
- feature importance
- grafik aktual versus prediksi
- keterangan periode training, validasi, dan test

Tab cuaca tetap bersifat opsional sampai dataset cuaca tersedia. Jika data cuaca berhasil digabungkan, analisis cuaca dapat ditambahkan sebagai tab atau subbagian tersendiri.
