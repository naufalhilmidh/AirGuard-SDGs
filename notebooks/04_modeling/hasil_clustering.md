# Ringkasan Hasil Clustering Kualitas Udara Pulau Jawa
**Proyek AirGuard SDGs: Pengelompokan 119 Kabupaten/Kota Berdasarkan Risiko Polusi**  
*Sumber Analisis: `notebooks/04_modeling/CLUSTERING.ipynb`*  
*Output Data: `data/data_gabungan/clustering_wilayah.csv`*

---

## 1. Sekilas Hasil

Melalui algoritma **K-Means Clustering** (dengan $k = 3$), **119 Kabupaten dan Kota di Pulau Jawa** berhasil dikelompokkan ke dalam 3 kelompok profil risiko polusi udara berdasarkan data historis 4 tahun (2022–2026):

1. **Cluster 0: "Rendah - Stabil" (49 Wilayah / 41.2%)**  
   Wilayah paling bersih dan aman. Sangat jarang mengalami hari polusi tinggi.
2. **Cluster 1: "Sedang - Musiman" (50 Wilayah / 42.0%)**  
   Wilayah dengan beban polusi moderat, namun rentan melonjak menjadi tidak sehat saat musim kemarau.
3. **Cluster 2: "Tinggi - Persisten" (20 Wilayah / 16.8%)**  
   Zona merah/darurat polusi udara dengan tingkat polusi tinggi yang berlangsung hampir sepanjang tahun (Jabodetabek dan kawasan industri sekitarnya).

---

## 2. Perbandingan Karakteristik Antar Cluster

| Indikator Utama | Cluster 0 (Rendah) | Cluster 1 (Sedang) | Cluster 2 (Tinggi) |
| :--- | :---: | :---: | :---: |
| **Jumlah Wilayah** | 49 Kota/Kab | 50 Kota/Kab | 20 Kota/Kab |
| **Rata-rata PM2.5** | **25.4 µg/m³** | **39.7 µg/m³** | **58.8 µg/m³** *(melebihi batas aman)* |
| **Persentase Hari Tidak Sehat (>55 µg/m³)** | **3.6%** (~13 hari/tahun) | **22.2%** (~81 hari/tahun) | **52.6%** (~192 hari/tahun) |
| **Frekuensi Episode Polusi** | Rata-rata 5.8 kali | Rata-rata 38.7 kali | Rata-rata 64.7 kali |
| **Durasi Polusi Terpanjang** | ~4 hari berturut-turut | ~30 hari berturut-turut | **~97 hari berturut-turut (>3 bulan)** |
| **Emisi Kendaraan & Industri (NO2 & CO)** | Sangat Rendah | Sedang | Sangat Tinggi (3–4x lipat Cluster 0) |

---

## 3. Detail Profil & Daftar Anggota Setiap Cluster

### 🟢 Cluster 0: Rendah - Stabil (Kawasan Bersih & Terjaga)
- **Karakteristik**: Kualitas udara relatif bersih dan stabil sepanjang tahun. Polusi tinggi hanya terjadi sesekali dan berlangsung singkat (rata-rata 4 hari).
- **Faktor Utama**: Didominasi kawasan pesisir pantai selatan, wilayah pegunungan, kawasan agraris, serta minim kawasan industri besar.
- **Sebaran Wilayah (49 Kota/Kab)**:
  - **Jawa Timur (25)**: Banyuwangi, Situbondo, Pamekasan, Sumenep, Bondowoso, Pacitan, Trenggalek, Blitar, Tulungagung, Jember, Tuban, Lumajang, Pasuruan (Kota & Kab), Probolinggo (Kota & Kab), Kediri (Kota & Kab), Blitar (Kota), Malang (Kota & Kab), Kota Batu.
  - **Jawa Tengah (13)**: Cilacap, Banyumas, Brebes, Tegal (Kota & Kab), Pemalang, Batang, Kota Pekalongan, Kendal, Kota Semarang, Blora, Jepara, Wonogiri.
  - **Jawa Barat (7)**: Tasikmalaya (Kota & Kab), Garut, Pangandaran, Indramayu, Kab. Sukabumi, Kab. Bandung.
  - **DI Yogyakarta (3)**: Kulon Progo, Bantul, Gunungkidul.
  - **DKI Jakarta (1)**: Kepulauan Seribu.

---

### 🟡 Cluster 1: Sedang - Musiman (Kawasan Penyangga & Transisi)
- **Karakteristik**: Udara berada di level sedang pada musim hujan, namun memburuk saat musim kemarau. Rata-rata 1 dari setiap 4 hari berada di atas baku mutu udara aman. Sekali terjadi polusi pekat, durasinya bisa bertahan rata-rata 1 bulan penuh berturut-turut.
- **Faktor Utama**: Koridor agraris padat penduduk dan kota-kota penyangga dengan aktivitas lalu lintas menengah.
- **Sebaran Wilayah (50 Kota/Kab)**:
  - **Jawa Tengah (22)**: Purworejo, Kebumen, Banjarnegara, Purbalingga, Wonosobo, Temanggung, Magelang (Kota & Kab), Boyolali, Klaten, Sukoharjo, Karanganyar, Kota Surakarta (Solo), Sragen, Grobogan, Demak, Kudus, Pati, Rembang, Kab. Semarang, Kota Salatiga, Kab. Pekalongan.
  - **Jawa Timur (13)**: Surabaya, Gresik, Sidoarjo, Mojokerto (Kota & Kab), Jombang, Nganjuk, Madiun (Kota & Kab), Ngawi, Magetan, Bojonegoro, Bangkalan.
  - **Jawa Barat (9)**: Ciamis, Kota Banjar, Majalengka, Kuningan, Cirebon (Kota & Kab), Sumedang, Cianjur, Kota Sukabumi.
  - **Banten (4)**: Serang (Kota & Kab), Kota Cilegon, Pandeglang.
  - **DI Yogyakarta (2)**: Kota Yogyakarta, Sleman.

---

### 🔴 Cluster 2: Tinggi - Persisten (Kawasan Kritis / Episentrum Polusi)
- **Karakteristik**: Zona polusi paling parah di Pulau Jawa. Lebih dari separuh hari dalam setahun (**52.6% hari**) kualitas udaranya berstatus tidak sehat. Rentetan hari polusi ekstrem rata-rata mencapai **97 hari berturut-turut** (di Kab. Bekasi bahkan mencapai 149 hari berturut-turut).
- **Faktor Utama**: Kepadatan lalu lintas megapolitan yang luar biasa tinggi dan konsentrasi kawasan industri manufaktur/PLTU.
- **Sebaran Wilayah (20 Kota/Kab - Seluruhnya Terkonsentrasi di Bagian Barat Jawa)**:
  - **DKI Jakarta (5)**: Jakarta Pusat, Jakarta Utara, Jakarta Barat, Jakarta Selatan, Jakarta Timur.
  - **Jawa Barat (11)**: Kota Depok, Kota Bekasi, Kab. Bekasi, Kota Bogor, Kab. Bogor, Kota Bandung, Kota Cimahi, Kab. Bandung Barat, Purwakarta, Subang, Karawang.
  - **Banten (4)**: Kota Tangerang, Kota Tangerang Selatan, Kab. Tangerang, Kab. Lebak.

---

## 4. Pola Geografis Antar Provinsi

| Provinsi | Cluster 0 (Rendah) | Cluster 1 (Sedang) | Cluster 2 (Tinggi) | Total Wilayah | Kesimpulan |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **DKI Jakarta** | 1 (Kep. Seribu) | 0 | **5** | 6 | Hampir seluruh wilayah masuk zona kritis |
| **Banten** | 0 | 4 | **4** | 8 | Terbagi antara zona sedang dan zona kritis |
| **Jawa Barat** | 7 | 9 | **11** | 27 | Didominasi wilayah sedang dan kritis |
| **Jawa Tengah** | 13 | **22** | **0** | 35 | **Bebas zona kritis** (didominasi sedang) |
| **Jawa Timur** | **25** | 13 | **0** | 38 | **Mayoritas bersih dan aman** |
| **DI Yogyakarta** | **3** | 2 | **0** | 5 | **Bebas zona kritis** (bersih hingga sedang) |
| **TOTAL** | **49** | **50** | **20** | **119** | — |

> **Pola Gradien Spasial (Barat ke Timur):**  
> Terdapat pola yang sangat mencolok: polusi parah terkonsentrasi kuat di ujung barat Pulau Jawa (Jabodetabek, sebagian Banten, dan koridor industri Jawa Barat). Semakin bergerak ke arah timur (Jateng, DIY, Jatim), kualitas udara berangsur jauh lebih baik dan tidak ada satupun wilayah di tiga provinsi tersebut yang masuk ke Cluster 2.

---

## 5. Validasi Hasil Menggunakan PCA (Principal Component Analysis)

Untuk memvalidasi dan memvisualisasikan hasil clustering dari 10 indikator ke dalam bentuk grafik 2 dimensi (2D), diterapkan teknik **PCA**:

- **Informasi Data Terjelaskan Sangat Tinggi (93.0%)**:
  - **PC1 (84.0% variansi)**: Menjadi sumbu utama *"Tingkat Keparahan Polusi Total"*. Ini membuktikan bahwa partikulat ($PM_{2.5}, PM_{10}$) dan gas emisi ($NO_2, CO$) bergerak searah seiring memburuknya kualitas udara.
  - **PC2 (9.0% variansi)**: Menangkap variasi sekunder berupa dinamika fluktuasi musiman.
- **Kesimpulan Visualisasi**:
  Plot 2D PCA menunjukkan bahwa **ketiga cluster terpisah secara sangat tegas dan bersih (*well-separated*)** tanpa ada pola tumpang tindih (*overlapping*), menegaskan bahwa pengelompokan 3 wilayah ini memiliki batas karakteristik yang nyata.

---

## 6. Pemanfaatan Hasil untuk Dashboard & Kebijakan (SDGs)

1. **Visualisasi Dashboard Interaktif AirGuard**:
   - Terapkan sistem warna peringatan (*traffic light*) pada peta wilayah:
     - 🟢 **Hijau (Cluster 0)**: Wilayah Rendah / Udara Sehat
     - 🟡 **Kuning (Cluster 1)**: Wilayah Sedang / Waspada Polusi Musim Kemarau
     - 🔴 **Merah (Cluster 2)**: Wilayah Tinggi / Prioritas Darurat Polusi
2. **Arah Kebijakan Publik Berbasis Bukti (SDGs 3 & 11)**:
   - **Cluster 2 (Prioritas Utama)**: Perlu penegakan uji emisi, perbaikan transportasi publik terintegrasi, dan pengawasan ketat emisi industri/pembangkit listrik.
   - **Cluster 1 (Antisipasi Musiman)**: Perlu sistem peringatan dini agar masyarakat dan pemerintah daerah bersiap sebelum musim kemarau tiba.
   - **Cluster 0 (Preservasi)**: Fokus pada perlindungan ruang terbuka hijau dan ekosistem agar kualitas udara yang bersih tetap terjaga.
