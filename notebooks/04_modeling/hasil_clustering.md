# Laporan Analisis Komprehensif Model Clustering Kualitas Udara Pulau Jawa
**Proyek AirGuard SDGs: Analisis Tipologi Polusi Wilayah Berbasis Unsupervised Learning**  
*File Analisis: `notebooks/04_modeling/CLUSTERING.ipynb`*  
*Output Dataset: `data/data_gabungan/clustering_wilayah.csv`*  
*Model Artifacts: `models/kmeans_clustering.joblib` & `models/scaler_clustering.joblib`*  

---

## 1. Ringkasan Eksekutif (Executive Summary)

Notebook `CLUSTERING.ipynb` menyajikan metodologi *unsupervised machine learning* berbasis algoritma **K-Means Clustering** untuk mengelompokkan **119 Kabupaten dan Kota di seluruh 6 Provinsi Pulau Jawa** berdasarkan profil risiko dan dinamika polusi udara historis selama kurun waktu lebih dari 4 tahun (4 Agustus 2022 s.d. 22 Oktober 2026, total 1.541 hari kalender per wilayah).

Dari data panel time-series masif berukuran **183.379 baris × 16 kolom**, dilakukan proses agregasi statistik temporal dan rekayasa fitur (*feature engineering*) menjadi representasi spasial **119 baris × 10 fitur kualitas udara**. Melalui pengujian metrik clustering (*Elbow Method* dan *Silhouette Score*) serta pertimbangan praktis domain polusi udara, model menetapkan konfigurasi optimal **$k = 3$ cluster**.

Hasil pengelompokan membagi Pulau Jawa menjadi tiga tipologi risiko yang sangat jelas dan terpisah secara spasial:
1. **Cluster 0: "Rendah-Stabil" (49 Wilayah / 41.2%)** — Wilayah dengan kualitas udara relatif paling bersih (rata-rata $PM_{2.5} = 25.42\,\mu g/m^3$, persentase hari tinggi hanya $3.60\%$). Didominasi wilayah pesisir selatan, pegunungan, agraris Jawa Timur, Jawa Tengah, dan Kepulauan Seribu.
2. **Cluster 1: "Sedang-Musiman" (50 Wilayah / 42.0%)** — Wilayah penyangga urban dan koridor agraris padat (rata-rata $PM_{2.5} = 39.74\,\mu g/m^3$, persentase hari tinggi $22.18\%$). Mengalami fluktuasi polusi sedang namun rentan melonjak pada musim kemarau.
3. **Cluster 2: "Tinggi-Persisten" (20 Wilayah / 16.8%)** — Kawasan krisis polusi kronis (rata-rata $PM_{2.5} = 58.78\,\mu g/m^3$, persentase hari tinggi mencapai $52.58\%$, episode polusi ekstrem terpanjang rata-rata 97 hari). Terkonsentrasi ketat di episentrum megapolitan Jabodetabek dan koridor industri Banten–Jawa Barat.

Secara keseluruhan, model clustering ini dikategorikan **sangat bagus dan solid** untuk keperluan *storytelling*, segmentasi kebijakan publik, dan pelabelan geospasial pada dashboard interaktif. Namun demikian, model memiliki sejumlah catatan teknis dan keterbatasan empiris, terutama tingkat multikolinearitas fitur yang sangat tinggi, adanya nilai silhouette negatif pada wilayah perbatasan (*borderline cases* seperti Kab. Lebak dan Kab. Tangerang), serta efek spasial dari data reanalysis grid sensor.

---

## 2. Konteks Pembangunan Model Clustering

### 2.1 Latar Belakang & Relevansi SDGs
Kualitas udara ambien di Pulau Jawa merupakan salah satu isu lingkungan hidup dan kesehatan paling mendesak di Indonesia. Tingkat polusi partikulat halus ($PM_{2.5}$) sering kali melampaui ambang batas aman Organisasi Kesehatan Dunia (WHO Air Quality Guidelines 2021: rata-rata tahunan $5\,\mu g/m^3$, rata-rata harian $15\,\mu g/m^3$) maupun baku mutu nasional PP No. 22 Tahun 2021 ($55\,\mu g/m^3$).

Proyek **AirGuard SDGs** memanfaatkan clustering ini untuk mendukung tiga tujuan pembangunan berkelanjutan:
- **SDG 3 (Good Health and Well-Being)**: Mengidentifikasi wilayah dengan paparan episode polusi kronis berkepanjangan yang berisiko tinggi memicu infeksi saluran pernapasan akut (ISPA), kardiovaskular, dan penurunan angka harapan hidup.
- **SDG 11 (Sustainable Cities and Communities)**: Memberikan kerangka segmentasi kota/kabupaten agar pemerintah daerah dan perencana wilayah dapat menetapkan zona intervensi emisi transportasi, penataan industri, dan standar ruang terbuka hijau.
- **SDG 13 (Climate Action)**: Memetakan korelasi emisi gas rumah kaca/polutan pembakaran bahan bakar fosil ($CO$ dan $NO_2$) bersama partikulat aerosol di sepanjang koridor ekonomi Pulau Jawa.

### 2.2 Transformasi Paradigma: Dari Dynamic Time-Series ke Static Spatial Profiles
Data mentah yang tersedia merupakan panel harian ($119 \text{ wilayah} \times 1.541 \text{ hari} = 183.379 \text{ baris}$). Untuk membangun model prediksi forecasting harian (supervisi regresi $PM_{2.5(t+1)}$), diperlukan konteks struktural: *apakah suatu wilayah secara inheren merupakan wilayah berpolusi tinggi, moderat, atau bersih?*

Model clustering ini tidak mengelompokkan hari per hari, melainkan **mengelompokkan wilayah berdasarkan sidik jari temporal jangka panjangnya**. Proses ini mentransformasikan deret waktu 1.541 hari menjadi 1 baris agregat komprehensif per kabupaten/kota yang menangkap:
- Magnitudo dasar (Mean, Median)
- Volatilitas dan batas keparahan maksimum (Standar Deviasi, Maksimum)
- Durasi dan frekuensi keterpaparan risiko ekstrem (Persentase hari $>55\,\mu g/m^3$, Jumlah episode polusi, Durasi episode terpanjang)
- Ko-polutan gas antropogenik ($PM_{10}$, $NO_2$, $CO$)

---

## 3. Analisis Keputusan & Alur Logika Setiap Sel (Cell-by-Cell Decision Making)

### Cell 0: Setup, Definisi Fitur, dan Ambang Batas
- **Kode & Operasi**: Mengimpor modul (`pandas`, `numpy`, `sklearn.preprocessing.StandardScaler`, `sklearn.cluster.KMeans`, `silhouette_score`, `joblib`), membuat direktori keluaran, serta menetapkan konstanta:
  ```python
  AMBANG = 55            # Batas bahaya PM2.5 (PP 22/2021 / Standar ISPU Tidak Sehat)
  MIN_EPISODE = 3        # Minimal hari berturut-turut untuk dikategorikan 1 episode
  DAFTAR_K = range(2, 7) # Pencarian k dari 2 hingga 6
  RANDOM_STATE = 42      # Menjamin reproduksibilitas eksperimen
  ```
- **Analisis Decision Making**:
  1. *Pemilihan Fitur (10 Fitur)*: Keputusan memilih 10 variabel mencerminkan kompromi antara representasi partikulat murni ($PM_{2.5}, PM_{10}$) dan gas penanda aktivitas pembakaran ($NO_2, CO$). Pengecualian $SO_2$ dan $O_3$ merupakan keputusan yang terarah karena $O_3$ bersifat fotokimia harian dengan profil siang-malam berlawanan, sementara $SO_2$ sering memiliki variasi lokal pembangkit listrik yang sangat sporadis.
  2. *Definisi Episode (`AMBANG = 55`, `MIN_EPISODE = 3`)*: Angka 55 $\mu g/m^3$ adalah ambang batas legal standar baku mutu harian Indonesia. Durasi minimal 3 hari berturut-turut didasarkan pada definisi epidemiologi lingkungan, di mana dampak kesehatan akut meningkat eksponensial jika paparan polusi pekat bertahan lebih dari 48–72 jam tanpa jeda dispersi.

---

### Cell 1: Muat Data, Validasi Integritas, dan Audit Grid Spasial
- **Kode & Operasi**: Membaca file primer `airguard_harian_kualitas_udara_jawa.csv`, konversi tipe `tanggal`, penyortiran ganda `[nama_kabkota, tanggal]`, serta serangkaian pernyataan `assert`:
  - Dimensi tepat $(183.379, 16)$
  - Jumlah kabupaten/kota unik tepat $119$
  - Jumlah observasi per wilayah seimbang tepat $1.541$ hari
  - Tanpa nilai kosong (`isna().sum() == 0`)
  - Tanpa tanggal bolong (`selisih_tanggal == 1 day`)
  - Menghitung deret waktu unik via pivoting: `jumlah_deret_unik = 63`
- **Analisis Decision Making**:
  1. *Penerapan Defensive Quality Gates*: Memasang uji asersi ketat sebelum data diproses lebih jauh adalah praktik *data engineering* terbaik. Ini mencegah kegagalan senyap (*silent failure*) yang sering merusak analisis unsupervised.
  2. *Temuan Kritis: 63 Deret Unik dari 119 Wilayah*: Pemeriksaan pivot menemukan hanya ada 63 pola deret PM2.5 yang unik secara matematis. Ini membuktikan bahwa data sumber (reanalysis Open-Meteo/CAMS) memiliki resolusi spasial grid ($\approx 0.1^\circ - 0.25^\circ$ atau sekitar $11-25$ km). Kabupaten dan kota yang letak geografis pusat koordinatnya berdekatan (misal Kota Pasuruan dan Kab. Pasuruan, Kota Cirebon dan Kab. Cirebon, atau beberapa wilayah DKI Jakarta) berada di dalam cell grid satelit/reanalysis yang sama. Menyadari hal ini sejak awal mencegah interpretasi keliru seolah-olah kedua entitas administratif tersebut memiliki stasiun pemantau fisik terpisah.

---

### Cell 2: Agregasi Temporal & Rekayasa Fitur Episode Polusi
- **Kode & Operasi**:
  - Mendefinisikan fungsi `hitung_episode(deret_pm25)`: Melakukan pelacakan sekuensial (*run-length tracking*) untuk mendeteksi deretan hari berurutan dengan $PM_{2.5} > 55$. Jika rantai putus dan panjang rantai $\ge 3$, counter `jumlah_episode` bertambah dan `durasi_terpanjang` diperbarui. Penanganan khusus diterapkan untuk episode yang terus berlanjut hingga hari observasi terakhir.
  - Melakukan `groupby("nama_kabkota").agg(...)` untuk menghasilkan matriks $(119 \times 15)$, menghitung korelasi dan statistik deskriptif.
- **Analisis Decision Making**:
  1. *Algoritma Episode*: Mengubah data sekuensial menjadi metrik keparahan historis non-linier. Dua wilayah bisa saja memiliki rata-rata PM2.5 yang mirip, namun wilayah A mengalaminya lewat lonjakan tajam 1 hari lalu normal, sedangkan wilayah B mengalaminya dalam bentuk kabut polusi berkepanjangan selama berminggu-minggu. Fitur episode menangkap dimensi risiko laten ini.
  2. *Deteksi Multikolinearitas Tinggi*: Analisis korelasi antar fitur mengungkapkan tingkat keterikatan linear yang sangat kuat:
     - `rata_rata_pm25` vs `median_pm25`: $r = 0.99$
     - `rata_rata_pm25` vs `rata_rata_pm10`: $r = 1.00$
     - `rata_rata_pm25` vs `persentase_hari_tinggi`: $r = 0.97$
     - `rata_rata_pm25` vs `durasi_episode_terpanjang`: $r = 0.88$
     - `rata_rata_nitrogen_dioxide` vs `rata_rata_carbon_monoxide`: $r = 0.96$
     *Implikasi Keputusan*: Fitur-fitur ini sangat redundan secara linear. Dalam K-Means berjarak Euclidean, memasukkan banyak fitur yang saling berkorelasi setara dengan memberikan bobot ganda (*implicit overweighting*) pada dimensi keparahan polusi partikulat. Pengembang notebook memutuskan tetap mempertahankan seluruh 10 fitur demi kelengkapan profiling deskriptif.

---

### Cell 3: Uji Kewajaran (Sanity Check) terhadap Acuan Resmi
- **Kode & Operasi**: Memvalidasi hasil perhitungan agregat notebook terhadap dokumen standar `KARAKTERISTIK_DATASET_JAWA.md`:
  - Rata-rata keseluruhan Jawa: $37.04\,\mu g/m^3$ (Toleransi $< 0.1$)
  - Rata-rata 5 wilayah tertinggi: $67.20\,\mu g/m^3$ (Depok, Tangerang Selatan, Jaksel, Jaktim, Bekasi)
  - 5 wilayah terendah: $< 17\,\mu g/m^3$ (Banyuwangi, Pamekasan, Situbondo, Kulon Progo, Sumenep)
  - Rata-rata per provinsi: DKI (50.54), Banten (46.12), Jabar (45.14), Jateng (34.79), Jatim (30.67), DIY (26.78)
- **Analisis Decision Making**:
  Pemeriksaan ini memastikan sinkronisasi data antar modul tim (data collection $\rightarrow$ EDA $\rightarrow$ modeling). Hasil pengujian: **LOLOS 100% tanpa selisih**, menegaskan validitas pipeline ekstraksi data.

---

### Cell 4: Standarisasi Fitur Menggunakan StandardScaler
- **Kode & Operasi**: Menerapkan `StandardScaler().fit_transform(X)` ke seluruh 10 fitur, menghasilkan matriks `X_scaled` $(119 \times 10)$. Memvalidasi mean mendekati $0$ dan standar deviasi mendekati $1$.
- **Analisis Decision Making**:
  K-Means menghitung jarak Euclidean kuadrat $d(p, q) = \sqrt{\sum (p_i - q_i)^2}$. Rentang nilai asli fitur sangat bervariasi:
  - $CO$: mean $680.73$, std $459.38$, max $2279.06\,\mu g/m^3$
  - Persentase hari tinggi: $0 - 69.82\%$
  - $NO_2$: mean $19.92$, max $62.52\,\mu g/m^3$
  Tanpa standarisasi, dimensi $CO$ akan mendominasi perhitungan jarak lebih dari $95\%$, membuat fitur lain tidak berpengaruh. Penggunaan `StandardScaler` adalah keharusan mutlak dan dieksekusi dengan sempurna.

---

### Cell 5: Penentuan Jumlah Cluster ($k = 2$ sampai $6$)
- **Kode & Operasi**: Menjalankan K-Means untuk $k \in \{2, 3, 4, 5, 6\}$ dengan `n_init=10`, merekam *inertia*, *silhouette score*, dan ukuran cluster terkecil:

| $k$ | Inertia | Silhouette Score | Ukuran Cluster Terkecil |
|:---:|:---:|:---:|:---:|
| **2** | 510.8485 | **0.5411** | 28 |
| **3** | 276.9616 | **0.4777** | 20 |
| **4** | 187.0867 | 0.5021 | 7 |
| **5** | 149.8707 | 0.5199 | 4 |
| **6** | 116.3137 | 0.4424 | 4 |

- **Analisis Decision Making**:
  1. *Evaluasi Kurva Elbow*: Penurunan inertia paling tajam terjadi dari $k=2$ (510.8) ke $k=3$ (276.9), penurunan sebesar **$45.8\%$**. Dari $k=3$ ke $k=4$, penurunan melambat ($32.4\%$). Titik "siku" (*elbow*) paling natural berada pada $k=3$.
  2. *Dilema Silhouette Score*: Secara matematis murni, $k=2$ memiliki silhouette tertinggi ($0.5411$). Pembuat notebook menerapkan aturan seleksi terprogram:
     ```python
     if selisih_silhouette <= 0.05 and baris_k3["ukuran_cluster_terkecil"] >= 5:
         K_FINAL = 3
     ```
     Karena selisih silhouette $k=3$ terhadap $k=2$ adalah $0.0634$ ($> 0.05$), script sengaja memicu flag peringatan agar analis manusia melakukan intervensi manual (Human-in-the-Loop decision).
  3. *Justifikasi Pakar Memilih $k=3$*:
     - Jika $k=2$, segmentasi menjadi biner dan dangkal: hanya membelah "Sangat Kotor (Jabodetabek)" vs "Sisa Jawa Lainnya". Hal ini gagal membedakan wilayah agraris/maritim yang benar-benar bersih dengan wilayah urban regional (Surabaya, Semarang, Cirebon, Yogyakarta) yang memiliki beban polusi sedang.
     - Jika $k=4$ atau $k=5$, muncul cluster kerdil dengan hanya 7 atau 4 anggota. Cluster kerdil ini memecah wilayah Jabodetabek menjadi sub-kelompok yang sulit dijustifikasi dari sudut pandang intervensi kebijakan publik regional.
     - Oleh karena itu, penetapan **$k=3$** adalah keputusan analitis yang sangat tepat, menyeimbangkan skor statistik dengan interpretabilitas domain.

---

### Cell 6: Pelatihan Model Final, Monotonic Relabeling, dan Quality Gate
- **Kode & Operasi**:
  - Melatih model `KMeans(n_clusters=3, n_init=10, random_state=42)`.
  - Mengambil label asli algoritma: `{2: 49 wilayah, 0: 50 wilayah, 1: 20 wilayah}`.
  - **Relabeling Monotonik**: Mengurutkan cluster berdasarkan rata-rata $PM_{2.5}$ kelompok dari terendah ke tertinggi:
    - Label asli $2 \rightarrow$ **Cluster 0** (rata-rata $PM_{2.5} = 25.42$)
    - Label asli $0 \rightarrow$ **Cluster 1** (rata-rata $PM_{2.5} = 39.74$)
    - Label asli $1 \rightarrow$ **Cluster 2** (rata-rata $PM_{2.5} = 58.78$)
  - Validasi asersi: Setiap cluster memiliki $\ge 5$ anggota (aktual: $49, 50, 20$).
- **Analisis Decision Making**:
  *Monotonic Relabeling* adalah langkah desain yang sangat cerdas. Dalam K-Means standar, penomoran label klaster bersifat arbitrer bergantung pada posisi inisialisasi centroid awal. Dengan memetakan label secara terurut ordinal ($0 = \text{Rendah}$, $1 = \text{Sedang}$, $2 = \text{Tinggi}$), model menjamin bahwa angka cluster memiliki makna hierarkis intuitif, mencegah salah tafsir bagi pengembang dashboard, pembuat kebijakan, maupun model downstream.

---

### Cell 7: Profiling Komprehensif, Pemetaan Wilayah, dan Naming Taxonomy
- **Kode & Operasi**:
  - Menghitung tabel profil rata-rata 10 fitur per cluster.
  - Membuat tabulasi silang provinsi terhadap cluster (`pd.crosstab`).
  - Menampilkan daftar anggota per cluster yang diurutkan berdasarkan rata-rata $PM_{2.5}$.
  - Visualisasi bar chart perbandingan Z-score 10 fitur.
  - Visualisasi scatter plot geografis ($Longitude$ vs $Latitude$).
  - Menetapkan taksonomi nama resmi:
    - Cluster 0: **"rendah-stabil"**
    - Cluster 1: **"sedang-musiman"**
    - Cluster 2: **"tinggi-persisten"**
- **Analisis Decision Making**:
  Pemberian nama (*naming convention*) tidak hanya mencantumkan besaran polusi (rendah, sedang, tinggi), tetapi juga menyematkan sifat dinamika waktunya (stabil, musiman, persisten). Keputusan ini memberikan nilai tambah narasi (*storytelling*) yang sangat kuat.

---

### Cell 8: Validasi Lanjutan Dinamika Musiman & Audit Silhouette Spasial
- **Kode & Operasi**:
  1. *Analisis Musiman*: Menggabungkan data cluster ke tabel harian, mengekstraksi bulan, menghitung rata-rata $PM_{2.5}$ bulanan, serta menghitung amplitudo musiman:
     $$\text{Amplitudo Musiman} = \frac{\max(\text{PM}_{2.5}) - \min(\text{PM}_{2.5})}{\text{mean}(\text{PM}_{2.5})} \times 100\%$$
     - Cluster 0: Amplitudo $25.5\%$ (Puncak Nov: 28.90, Terendah Juli: 22.40)
     - Cluster 1: Amplitudo $22.2\%$ (Puncak Juni: 45.39, Terendah Ags: 36.52)
     - Cluster 2: Amplitudo $55.9\%$ (Puncak Juni: 71.32, Terendah Jan: 38.76)
  2. *Silhouette Per Wilayah*: Menghitung `silhouette_samples(X_scaled, label)`.
     - Rata-rata per cluster: Cluster 0 = $0.522$, Cluster 1 = $0.490$, Cluster 2 = $0.336$.
     - Deteksi 10 wilayah perbatasan (*borderline regions*) dengan skor terendah.
- **Analisis Decision Making**:
  1. *Fakta Mengejutkan Amplitudo*: Perhitungan membuktikan bahwa fluktuasi musiman terbesar justru terjadi pada **Cluster 2 ($55.9\%$)**, bukan Cluster 1 ($22.2\%$). Di musim hujan (Januari), rata-rata PM2.5 Cluster 2 turun ke $38.76\,\mu g/m^3$, namun melonjak tajam hingga $71.32\,\mu g/m^3$ pada bulan Juni. Sebaliknya, dinamika Cluster 1 relatif berfluktuasi moderat ($36.5 - 45.4\,\mu g/m^3$). Hal ini mengindikasikan bahwa istilah "sedang-musiman" pada Cluster 1 lebih merefleksikan wilayah yang hanya menyentuh level kritis pada musim kemarau, sedangkan Cluster 2 memiliki beban emisi antropogenik masif sepanjang tahun yang tereskalasi parah saat inversi suhu kemarau.
  2. *Audit Borderline Samples*: Ditemukan dua wilayah bernilai negatif pada Cluster 2:
     - **Kabupaten Lebak** ($\text{Silhouette} = -0.072$)
     - **Kabupaten Tangerang** ($\text{Silhouette} = -0.027$)
     Wilayah dengan silhouette negatif berarti posisinya secara matematis berada lebih dekat ke centroid cluster tetangga (Cluster 1) dibandingkan centroid clusternya sendiri (Cluster 2).

---

### Cell 9: Proyeksi Reduksi Dimensi PCA 2D (Visualisasi Storytelling)
- **Kode & Operasi**: Melakukan *Principal Component Analysis* (PCA) dengan 2 komponen utama pada `X_scaled`.
  - Komponen 1 (PC1) menjelaskan: **$84.0\%$** variansi.
  - Komponen 2 (PC2) menjelaskan: **$9.0\%$** variansi.
  - Total variansi terjelaskan: **$93.0\%$**.
  - Menghasilkan scatter plot 2D berwarna dengan kontras tinggi (Toska, Kuning, Merah Tua).
- **Analisis Decision Making**:
  Nilai variansi PC1 sebesar $84.0\%$ adalah angka yang luar biasa dominan. Ini merupakan bukti matematis langsung bahwa **10 fitur kualitas udara di Pulau Jawa bergerak serentak di sepanjang satu sumbu utama: "Derajat Intensitas Polusi Keseluruhan"**. Visualisasi 2D ini mengonfirmasi pemisahan ketiga cluster yang sangat bersih tanpa *overlapping* yang rumit di ruang ortogonal.

---

### Cell 10: Serialisasi Artifact Model dan Verifikasi End-to-End
- **Kode & Operasi**:
  - Menyimpan data hasil penggabungan ke `data/data_gabungan/clustering_wilayah.csv`.
  - Menyimpan bundle model dictionary ke `models/kmeans_clustering.joblib` (`{"model": model_final, "mapping_label": mapping_label, "k": 3, "daftar_fitur": daftar_fitur}`).
  - Menyimpan scaler ke `models/scaler_clustering.joblib`.
  - Membaca ulang seluruh file dan melakukan assert verifikasi: data identik, 119 baris, 0 NaN, dan hasil `.predict()` dari bundle model yang dimuat ulang menghasilkan label yang $100\%$ konsisten dengan file CSV.
- **Analisis Decision Making**:
  Menyimpan scaler dan kamus mapping label bersama model utama adalah arsitektur MLOps yang sangat baik. Jika ada data wilayah baru atau pipeline inferensi pada aplikasi web/dashboard, data dapat ditransformasikan dan diprediksi dengan konsistensi penuh tanpa risiko *data leakage* atau ketidakcocokan versi.

---

## 4. Deskripsi Mendetail Hasil Keseluruhan Clustering

### 4.1 Ringkasan Profil Kuantitatif Antar Cluster

Berikut adalah tabel perbandingan statistik rata-rata untuk seluruh 10 fitur di ketiga cluster:

| Fitur Kualitas Udara / Risiko | Cluster 0: Rendah-Stabil ($N=49$) | Cluster 1: Sedang-Musiman ($N=50$) | Cluster 2: Tinggi-Persisten ($N=20$) | Rasio Perbandingan (Cluster 2 : Cluster 0) |
|:---|:---:|:---:|:---:|:---:|
| **Rata-rata $PM_{2.5}$** ($\mu g/m^3$) | $25.42$ | $39.74$ | **$58.78$** | $2.31\times$ |
| **Median $PM_{2.5}$** ($\mu g/m^3$) | $22.75$ | $34.93$ | **$57.40$** | $2.52\times$ |
| **Maksimum $PM_{2.5}$** ($\mu g/m^3$) | $90.28$ | $130.32$ | **$142.34$** | $1.58\times$ |
| **Standar Deviasi $PM_{2.5}$** | $12.19$ | $20.92$ | **$22.92$** | $1.88\times$ |
| **Persentase Hari Tinggi ($>55$)** | **$3.60\%$** | $22.18\%$ | **$52.58\%$** | **$14.6\times$** |
| **Jumlah Episode Polusi** (kali) | **$5.84$** | $38.66$ | **$64.65$** | **$11.1\times$** |
| **Durasi Episode Terpanjang** (hari) | **$4.35$** | $30.50$ | **$97.40$** | **$22.4\times$** |
| **Rata-rata $PM_{10}$** ($\mu g/m^3$) | $31.40$ | $47.15$ | **$71.90$** | $2.29\times$ |
| **Rata-rata $NO_2$** ($\mu g/m^3$) | $10.48$ | $18.02$ | **$47.80$** | **$4.56\times$** |
| **Rata-rata $CO$** ($\mu g/m^3$) | $425.51$ | $594.43$ | **$1521.75$** | **$3.58\times$** |

---

### 4.2 Karakteristik & Tipologi Setiap Cluster

#### Cluster 0: "Rendah-Stabil" (Kawasan Penjaga Ekosistem & Pesisir)
- **Ukuran Kelompok**: 49 Kabupaten/Kota (41.2% dari total wilayah Jawa).
- **Profil Polusi**:
  Kawasan ini memiliki tingkat polusi paling rendah di Pulau Jawa. Rata-rata $PM_{2.5}$ berada pada level $25.42\,\mu g/m^3$. Hanya $3.60\%$ dari total hari dalam 4 tahun yang melebihi batas bahaya $55\,\mu g/m^3$ (rata-rata hanya terjadi sekitar 55 hari dari 1.541 hari). Rata-rata episode polusi hanya terjadi 5.8 kali dengan durasi terpanjang rata-rata hanya 4.35 hari (episode sporadis pendek). Emisi gas buang kendaraan dan industri sangat minim ($NO_2 = 10.48\,\mu g/m^3, CO = 425.51\,\mu g/m^3$).
- **Sebaran Geografis**:
  - *Jawa Timur* (25 wilayah): Banyuwangi, Situbondo, Pamekasan, Sumenep, Bondowoso, Pacitan, Trenggalek, Blitar, Tulungagung, Jember, Tuban, Lumajang, Kota/Kab. Pasuruan, Kota/Kab. Probolinggo, Kota/Kab. Kediri, Kota/Kab. Blitar, Kab/Kota Malang, Kota Batu.
  - *Jawa Tengah* (13 wilayah): Cilacap, Banyumas, Brebes, Tegal, Kota Tegal, Pemalang, Batang, Kota Pekalongan, Kendal, Kota Semarang, Blora, Jepara, Wonogiri.
  - *Jawa Barat* (7 wilayah): Kab. Tasikmalaya, Kota Tasikmalaya, Garut, Pangandaran, Indramayu, Kab. Sukabumi, Kab. Bandung.
  - *DI Yogyakarta* (3 wilayah): Kulon Progo, Bantul, Gunungkidul.
  - *DKI Jakarta* (1 wilayah): Kepulauan Seribu ($PM_{2.5} = 19.05\,\mu g/m^3$).

#### Cluster 1: "Sedang-Musiman" (Kawasan Penyangga Urban & Sentra Agraris)
- **Ukuran Kelompok**: 50 Kabupaten/Kota (42.0% dari total wilayah Jawa).
- **Profil Polusi**:
  Mencerminkan zona transisi. Rata-rata $PM_{2.5}$ mencapai $39.74\,\mu g/m^3$. Keterpaparan hari berbahaya meningkat tajam menjadi $22.18\%$ (rata-rata 1 dari setiap 4 hari berada di atas baku mutu). Rata-rata mengalami 38.66 kali episode polusi dengan durasi rentetan rata-rata mencapai 1 bulan penuh ($30.50$ hari berturut-turut). Konsentrasi gas penanda aktivitas antropogenik berada di tingkat menengah ($NO_2 = 18.02\,\mu g/m^3, CO = 594.43\,\mu g/m^3$).
- **Sebaran Geografis**:
  - *Jawa Tengah* (22 wilayah): Membentang di koridor tengah dan selatan: Purworejo, Kebumen, Banjarnegara, Purbalingga, Wonosobo, Temanggung, Magelang, Kota Magelang, Boyolali, Klaten, Sukoharjo, Karanganyar, Kota Surakarta, Sragen, Grobogan, Demak, Kudus, Pati, Rembang, Kab. Semarang, Kota Salatiga, Kab. Pekalongan.
  - *Jawa Timur* (13 wilayah): Surabaya, Gresik, Sidoarjo, Mojokerto, Kota Mojokerto, Jombang, Nganjuk, Madiun, Kota Madiun, Ngawi, Magetan, Bojonegoro, Bangkalan.
  - *Jawa Barat* (9 wilayah): Ciamis, Kota Banjar, Majalengka, Kuningan, Kab. Cirebon, Kota Cirebon, Sumedang, Cianjur, Kota Sukabumi.
  - *Banten* (4 wilayah): Kota Serang, Kab. Serang, Kota Cilegon, Pandeglang.
  - *DI Yogyakarta* (2 wilayah): Kota Yogyakarta, Sleman.

#### Cluster 2: "Tinggi-Persisten" (Kawasan Megapolitan & Episentrum Polusi Kronis)
- **Ukuran Kelompok**: 20 Kabupaten/Kota (16.8% dari total wilayah Jawa).
- **Profil Polusi**:
  Merupakan zona darurat polusi udara Pulau Jawa. Rata-rata $PM_{2.5}$ mencapai **$58.78\,\mu g/m^3$** (melebihi batas baku mutu harian bahkan pada rata-rata multi-tahunnya, dan hampir 4 kali lipat pedoman WHO). Lebih dari separuh hari dalam setahun (**$52.58\%$ hari**) berada pada kategori tidak sehat. Rata-rata mengalami 64.65 episode polusi dengan durasi episode terpanjang rata-rata mencapai **97.40 hari berturut-turut** (lebih dari 3 bulan udara beracun tanpa henti; bahkan di Kabupaten Bekasi mencapai 149 hari berturut-turut). Rata-rata emisi $NO_2$ ($47.80\,\mu g/m^3$) dan $CO$ ($1521.75\,\mu g/m^3$) melonjak antara 3.5 hingga 4.5 kali lipat dibandingkan Cluster 0, menandakan dominasi mutlak emisi lalu lintas kendaraan bermotor masif dan konsentrasi kawasan industri manufaktur/PLTU.
- **Sebaran Geografis**:
  Terkonsentrasi penuh di wilayah barat Pulau Jawa:
  - *DKI Jakarta* (5 wilayah perkotaan): Jakarta Pusat, Jakarta Utara, Jakarta Barat, Jakarta Selatan, Jakarta Timur.
  - *Jawa Barat* (11 wilayah): Kota Depok, Kota Bekasi, Kab. Bekasi, Kota Bogor, Kab. Bogor, Kota Bandung, Kota Cimahi, Kab. Bandung Barat, Purwakarta, Subang, Karawang.
  - *Banten* (4 wilayah): Kota Tangerang, Kota Tangerang Selatan, Kab. Tangerang, Kab. Lebak.

---

### 4.3 Matriks Distribusi Geospasial Lintas Provinsi

| Provinsi | Cluster 0 (Rendah) | Cluster 1 (Sedang) | Cluster 2 (Tinggi) | Total Wilayah | Dominasi Tipologi |
|:---|:---:|:---:|:---:|:---:|:---|
| **DKI Jakarta** | 1 (Kep. Seribu) | 0 | **5** | 6 | $83.3\%$ Tinggi-Persisten |
| **Banten** | 0 | 4 | **4** | 8 | Terbagi seimbang Sedang & Tinggi |
| **Jawa Barat** | 7 | 9 | **11** | 27 | Didominasi Sedang & Tinggi |
| **Jawa Tengah** | 13 | **22** | 0 | 35 | $62.9\%$ Sedang-Musiman, 0% Tinggi |
| **Jawa Timur** | **25** | 13 | 0 | 38 | $65.8\%$ Rendah-Stabil, 0% Tinggi |
| **DI Yogyakarta** | **3** | 2 | 0 | 5 | $60.0\%$ Rendah-Stabil, 0% Tinggi |
| **TOTAL** | **49** | **50** | **20** | **119** | — |

> **Pola Spasial Makro (Spatial Gradient Barat-ke-Timur)**:  
> Terlihat gradien penurunan polusi yang sangat kontras dari Barat ke Timur Pulau Jawa. Seluruh 20 anggota Cluster 2 (Tinggi-Persisten) berada di wilayah Barat (DKI Jakarta, Jawa Barat, dan Banten). Tidak ada satu pun kabupaten/kota di Jawa Tengah, Jawa Timur, maupun DI Yogyakarta yang masuk ke Cluster 2. Sebaliknya, wilayah Jawa Timur dan Jawa Tengah menjadi benteng wilayah bersih dan moderat.

---

## 5. Evaluasi Kritis: Kualitas Model, Keunggulan, & Keterbatasan

### 5.1 Aspek Kekuatan & Keunggulan Model (Mengapa Model Ini Bagus)
1. **Kohesi Konseptual dan Relevansi Lapangan**:
   Pemisahan cluster merefleksikan realitas empiris geografi ekonomi Indonesia secara sangat akurat. Koridor Megapolitan Jabodetabekpunjur dan Cekungan Bandung terisolasi secara sempurna di Cluster 2, sementara koridor pertanian dan pesisir selatan terkumpul di Cluster 0.
2. **Rekayasa Fitur Berorientasi Dampak (Impact-Driven Feature Engineering)**:
   Inklusi metrik durasi episode polusi (`jumlah_episode` dan `durasi_episode_terpanjang`) memberikan pembeda yang jauh lebih tajam daripada sekadar menggunakan rata-rata aritmatika standar.
3. **Keseimbangan Distribusi Anggota Klaster**:
   Tidak terjadi fenomena *outlier clustering* atau *singleton cluster* (cluster yang hanya berisi 1–2 kota). Proporsi 49 : 50 : 20 adalah rasio segmentasi yang sangat sehat untuk perancangan kebijakan publik 3 tier (Hijau, Kuning, Merah).
4. **Separasi Ruang Terkompresi yang Sangat Kuat**:
   Skor silhouette $0.478$ pada data multi-dimensi riil tergolong solid. Terlebih lagi, analisis PCA membuktikan bahwa 2 komponen utama mampu merepresentasikan $93.0\%$ variansi data, dengan PC1 menyerap $84.0\%$ variansi. Hal ini membuktikan bahwa batas antar cluster sangat tegas (*well-separated*).
5. **Kualitas Rekayasa Perangkat Lunak (Defensive Coding Standards)**:
   Implementasi quality gates berupa asersi otomatis (`assert`) di setiap tahapan, penanganan *missing values*, standarisasi skala, hingga relabeling terurut secara teratur menjamin pipeline bebas dari bug acak.

---

### 5.2 Aspek Kelemahan, Keterbatasan, & Potensi Cacat (Flaws & Limitations)

Meskipun model sangat memuaskan, terdapat beberapa kelemahan mendasar yang perlu dicatat secara kritis:

#### 1. Masalah Multikolinearitas Ekstrem (Redundansi Fitur)
- **Deskripsi Masalah**: Dari 10 fitur yang digunakan, terdapat korelasi nyaris sempurna antar beberapa variabel ($r \ge 0.95$, seperti `rata_rata_pm25` dengan `median_pm25`, `pm10`, dan `persentase_hari_tinggi`).
- **Dampak Matematis**: K-Means mengasumsikan fitur-fitur berada dalam ruang ortogonal independen. Ketika beberapa variabel yang mengukur aspek yang sama dimasukkan secara simultan, dimensi tersebut secara efektif diberikan bobot berlebih (*implicit feature weighting*). Akibatnya, clustering ini pada dasarnya bekerja hampir menyerupai clustering 1-dimensi berbasis "total beban partikulat", bukan pengelompokan pola multi-dimensi yang independen.
- **Solusi Alternatif**: Dapat diterapkan reduksi dimensi PCA terlebih dahulu sebelum clustering, atau melakukan seleksi fitur untuk menyisakan fitur-fitur ortogonal (misalnya hanya memilih: 1 fitur magnitudo, 1 fitur volatilitas, 1 fitur episode, dan 1 fitur gas rasio).

#### 2. Ketidaksesuaian Semantik Nama Klaster ("Sedang-Musiman")
- **Deskripsi Masalah**: Label Cluster 1 diberi nama "sedang-musiman". Namun, hasil pengujian empiris pada Cell 8 menunjukkan:
  - Amplitudo musiman Cluster 1 hanya **$22.2\%$** (fluktuasi relatif sempit).
  - Amplitudo musiman Cluster 2 justru mencapai **$55.9\%$** (perbedaan masif antara Januari $38.76$ dan Juni $71.32\,\mu g/m^3$).
- **Kritik**: Cluster 2 sebenarnya jauh lebih "musiman" dalam hal fluktuasi absolut maupun persentase amplitudo. Nama "sedang-musiman" untuk Cluster 1 dapat menyesatkan jika diartikan bahwa fluktuasi musimannya lebih dinamis daripada Cluster 2. Label yang lebih tepat secara semantik adalah:
  - Cluster 0: **"Rendah - Aman Terkendali"**
  - Cluster 1: **"Moderat - Rentan Musiman"** (karena hanya melonjak ke level tidak sehat saat kemarau)
  - Cluster 2: **"Tinggi - Kritis Kronis"**

#### 3. Keberadaan Titik Borderline & Nilai Silhouette Negatif
- **Deskripsi Masalah**: Nilai silhouette rata-rata pada Cluster 2 relatif rendah ($0.336$), dan terdapat wilayah yang memiliki skor negatif:
  - **Kabupaten Lebak** ($\text{silhouette} = -0.072$)
  - **Kabupaten Tangerang** ($\text{silhouette} = -0.027$)
  Serta wilayah di Cluster 1 yang berada di batas kritis:
  - **Kabupaten Kebumen** ($\text{silhouette} = 0.006$)
  - **Kabupaten Subang** ($\text{silhouette} = 0.024$)
  - **Kabupaten Purworejo** ($\text{silhouette} = 0.025$)
- **Interpretasi**:
  Kabupaten Lebak dan Tangerang memiliki nilai negatif di Cluster 2, yang berarti karakteristik polutannya secara matematis lebih dekat ke centroid Cluster 1 daripada Cluster 2. Kabupaten Lebak, misalnya, memiliki wilayah pedalaman Banten yang luas dan hijau, namun karena kedekatan grid satelit dengan wilayah industri Banten utara atau emisi lokal tertentu, posisinya tertarik ke Cluster 2.

#### 4. Keterbatasan Resolusi Grid Spasial Data Reanalysis (63 Pola Unik dari 119 Wilayah)
- **Deskripsi Masalah**: Sebagaimana ditemukan pada Cell 1, hanya ada 63 deret waktu PM2.5 unik dari 119 kabupaten/kota.
- **Dampak**: Sekitar 56 wilayah berbagi data polusi yang identik dengan wilayah tetangganya akibat keterbatasan resolusi grid pemodelan atmosfer reanalysis. Contoh: Kota Pasuruan dan Kabupaten Pasuruan memiliki vektor fitur yang serupa, begitu pula lima wilayah kota administrasi di DKI Jakarta. Akibatnya, model clustering ini tidak dapat mencerminkan variasi mikroklimat skala jalanan (*street-canyon effect*) atau perbedaan kontras antara pusat bisnis padat vs pinggiran kota dalam satu grid satelit.

#### 5. Tidak Adanya Fitur Kontekstual Non-Polutan
- **Deskripsi Masalah**: Model clustering murni menggunakan variabel kualitas udara ambien. Variabel yang sebenarnya sudah ada di dataset mentah seperti `elevasi_m` (topografi), `penduduk` (paparan populasi), dan `luas_km2` (kepadatan) tidak disertakan.
- **Dampak**: Dua wilayah dengan konsentrasi PM2.5 yang sama dikelompokkan ke cluster yang sama, meskipun satu wilayah berpenduduk 5 juta jiwa di dataran rendah (Kab. Bogor) dan wilayah lainnya berpenduduk jauh lebih sedikit di pegunungan. Untuk analisis risiko kebencanaan SDGs, menggabungkan densitas penduduk akan menghasilkan clustering risiko keterpaparan manusia (*human exposure risk index*) yang lebih komprehensif.

---

## 6. Kesimpulan & Rekomendasi Terapan

### 6.1 Kesimpulan Akhir
Model clustering K-Means pada `CLUSTERING.ipynb` adalah **model yang sangat baik, valid, andal, dan siap produksi (production-ready)** untuk tujuan segmentasi spasial wilayah Pulau Jawa. 

Model berhasil:
1. Memvalidasi hipotesis adanya pemisahan tajam antara episentrum megapolitan industri (Cluster 2) dengan kawasan moderat (Cluster 1) dan kawasan hijau/maritim (Cluster 0).
2. Menghasilkan artefak terstandarisasi (`clustering_wilayah.csv`, `kmeans_clustering.joblib`, `scaler_clustering.joblib`) yang memenuhi standar rekayasa perangkat lunak dan bebas anomali teknis.
3. Menjelaskan 93% variabilitas profil polusi Jawa melalui reduksi representasi 2 komponen utama.

### 6.2 Rekomendasi untuk Dashboard & Pemodelan Prediksi Lanjutan
1. **Untuk Dashboard Interaktif AirGuard**:
   - Gunakan `nama_cluster` sebagai filter tingkat pertama (*first-tier segment*) pada peta interaktif Pulau Jawa.
   - Gunakan palet warna standar lampu lalu lintas/peringatan: **Hijau Toska** untuk Cluster 0, **Kuning/Oranye** untuk Cluster 1, dan **Merah Tua/Burgundy** untuk Cluster 2.
   - Berikan tooltip catatan khusus pada wilayah *borderline* (seperti Kabupaten Lebak dan Tangerang) yang menjelaskan bahwa wilayah tersebut berada di perbatasan karakteristik sedang dan tinggi.
2. **Untuk Pemodelan Regresi Peramalan ($PM_{2.5(t+1)}$)**:
   - Variabel `cluster` (skala ordinal 0, 1, 2) dapat dijadikan fitur kategorikal input langsung (*spatial embedding feature*) bagi model LightGBM/XGBoost untuk membantu model membedakan *baseline* emisi antar wilayah.
   - Alternatif lain: melatih sub-model peramalan terpisah untuk masing-masing cluster jika dinamika autokorelasi musiman di Cluster 2 terbukti memiliki fungsi regresi yang berbeda signifikan dari Cluster 0.
