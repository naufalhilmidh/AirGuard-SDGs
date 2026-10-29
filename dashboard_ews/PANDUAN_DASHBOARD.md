# AirGuard SDGs, Dashboard 2 (EWS, Proyeksi, Analitik)

Dashboard Streamlit untuk memprediksi PM2.5 hari berikutnya dan memberi peringatan dini kualitas udara di kabupaten/kota Pulau Jawa. Data berasal dari Open-Meteo yang diolah tim pemodelan.

Dokumen ini menjelaskan isi tiap halaman, fungsinya, dan siapa yang memakainya, supaya seluruh anggota tim punya gambaran yang sama.

> **Penting:** selama file hasil tim belum ada di `data/data_gabungan/`, semua angka yang tampil adalah **data contoh buatan (sintetis)**. Angka itu hanya untuk mengisi tampilan dan tidak boleh dikutip sebagai hasil penelitian.

---

## 1. Cara menjalankan

Dari akar repo:

```bash
python -m pip install -r dashboard_ews/requirements.txt
python -m streamlit run dashboard_ews/app.py
```

Buka `http://localhost:8501`. Jalankan selalu dari akar repo, bukan dari dalam folder `dashboard_ews`.

Versi online (Streamlit Cloud): branch `dashboard-streamlit`, main file `dashboard_ews/app.py`.

## 2. Alur pengguna

1. Pengguna tiba di **Landing page** (tanpa menu).
2. Klik **Masuk ke dashboard**. Sidebar kiri muncul dengan tiga halaman: EWS Harian, Proyeksi, Analitik & Evaluasi.
3. Tombol **Kembali ke beranda** di sidebar membawa pengguna ke landing lagi.

| Halaman | Untuk siapa | Pertanyaan yang dijawab |
|---|---|---|
| Landing page | Semua pengunjung | Dashboard ini tentang apa dan mencakup apa saja? |
| EWS Harian (H+1) | Masyarakat, rumah sakit, dinas lingkungan hidup | Bagaimana kualitas udara besok dan daerah mana yang perlu diwaspadai? |
| Proyeksi 2027 | Bappeda, perencana tata kota, peneliti | Bulan apa pada tahun depan yang cenderung paling buruk? |
| Analitik & Evaluasi | Dosen dan tim peneliti | Seberapa akurat model, di mana ia lemah, dan pola apa yang ada di data? |

## 3. Tiga status EWS

Dashboard memakai tiga status berdasarkan PM2.5 (µg/m³):

| Status | Sebutan | Rentang PM2.5 | Warna |
|---|---|---|---|
| 0 | Baik | Sampai 15,0 | Hijau |
| 1 | Sedang | 15,1 sampai 55,0 | Kuning |
| 2 | Tidak sehat | Di atas 55,0 | Merah |

Batas ini ada di `data.py` (`BATAS = [15.0, 55.0]`). Mengubahnya di satu tempat mengubah seluruh dashboard. **Nilai ambang perlu diverifikasi tim ke Permen LHK No. 14/2020** sebelum dipakai di laporan.

---

## 4. Landing page (`halaman_beranda.py`)

Halaman pembuka yang menjelaskan konteks proyek.

- **Hero:** judul, ringkasan cakupan, dan tombol **Masuk ke dashboard**.
- **Panel pratinjau (kanan hero):** jumlah kabupaten/kota per status untuk besok, dan empat daerah dengan prediksi PM2.5 tertinggi. Dihitung langsung dari data, jadi ikut berubah.
- **Empat angka besar:** jumlah kabupaten/kota dan provinsi, penduduk yang tercakup, jumlah hari data historis, dan kecocokan status EWS (persentase hari ketika status prediksi sama dengan status sebenarnya).
- **Tiga cara memakai dashboard:** kartu ringkas untuk masyarakat, perencana, dan peneliti.
- **Cara membaca status:** tiga kartu status beserta rentang PM2.5 dan saran singkat.
- **Kaitan dengan SDGs:** SDG 3 (kesehatan), SDG 11 (kota berkelanjutan), SDG 13 (iklim).

## 5. EWS Harian H+1 (`halaman_ews.py`)

Halaman untuk melihat kondisi udara **besok**. Angka besok adalah prediksi model, sedangkan angka hari ini adalah data aktual terakhir.

- **Filter:** provinsi, kabupaten/kota untuk kartu detail, dan tombol **Unduh status besok (CSV)**.
- **Empat kartu ringkasan:** jumlah wilayah dipantau, serta jumlah wilayah berstatus Baik, Sedang, dan Tidak sehat. Lencana kecil menunjukkan selisih terhadap hari ini (misalnya "+1 dari hari ini").
- **Status kota-kota besar besok:** enam kota berpenduduk terbanyak, dengan nilai PM2.5 dan status.
- **Peta risiko besok:** satu titik per kabupaten/kota, diwarnai menurut status prediksi. Lingkaran biru menandai daerah yang dipilih.
- **Kartu detail daerah (gelap):** status dan nilai prediksi besok, PM2.5 hari ini, perubahan, kecepatan angin, dan ventilasi udara. Ventilasi dihitung dari kecepatan angin: di bawah 7,2 km/jam dianggap lemah, 7,2 sampai 14,4 sedang, di atas itu baik. Batas ini hanya indikatif. Ada juga rekomendasi singkat sesuai status, yang bukan saran medis.
- **Prediksi tertinggi besok:** sepuluh kabupaten/kota dengan prediksi tertinggi pada filter yang dipilih, lengkap dengan batang mini dan lencana status.

## 6. Proyeksi (`halaman_proyeksi.py`)

Halaman untuk melihat **bulan-bulan yang cenderung tinggi** pada tahun depan. Ini bukan ramalan harian.

- **Cara proyeksi dibuat:** jika file prakiraan tim (`airguard_forecast.csv`) belum ada, dashboard memakai **pola musiman**: rata-rata PM2.5 per kabupaten/kota untuk tiap hari dalam setahun, dihaluskan 15 hari, dengan pita ±1 simpangan baku. Cara ini belum memperhitungkan tren jangka panjang, perubahan kebijakan, atau kejadian khusus seperti kebakaran lahan. Jika file tim ada, file itu yang dipakai.
- **Empat kartu ringkasan:** puncak proyeksi bulanan, bulan paling berisiko, provinsi paling berisiko, dan jumlah provinsi yang punya bulan di atas batas Tidak sehat.
- **Tren PM2.5 jangka panjang:** pilih provinsi atau kabupaten/kota. Garis abu-abu adalah data aktual 120 hari terakhir, garis biru proyeksi, pita biru muda rentang harian yang wajar, garis merah putus-putus batas 55 µg/m³, dan warna latar menandai musim (kemarau, hujan, pancaroba).
- **Kalender risiko polusi:** rata-rata proyeksi per bulan, diwarnai menurut status. Baris bisa provinsi atau kabupaten/kota pilihan.
- **Rekomendasi kebijakan daerah (gelap):** teks yang dihasilkan otomatis dari angka proyeksi, misalnya bulan dan provinsi yang melewati batas, serta kebutuhan melengkapi data. Ini bahan diskusi, bukan keputusan kebijakan.
- **Unduh CSV:** proyeksi bulanan per provinsi.

## 7. Analitik & Evaluasi (`halaman_analitik.py`)

Halaman untuk dosen dan tim peneliti. Semua metrik dihitung dari file prediksi yang punya nilai aktual. Di bagian atas ada pilihan **Cakupan analisis** (semua provinsi atau satu provinsi) yang memengaruhi seluruh halaman.

**Temuan utama (kartu gelap)** adalah ringkasan otomatis: rata-rata galat dan bias, perbandingan dengan tebakan sederhana, provinsi dan bulan yang paling sulit, persentase hari Tidak sehat yang berhasil diperingatkan, dan variabel cuaca yang paling berkaitan dengan PM2.5. Teks ini dibuat otomatis dan harus dicek dan ditafsirkan peneliti. Hubungan dengan cuaca adalah pola yang berkaitan, bukan bukti sebab-akibat.

Halaman ini punya tiga tab:

### Tab Evaluasi model
- **Kartu MAE, RMSE, R², Bias.** Kartu MAE menampilkan lencana perbandingan dengan *persistence* (tebakan "besok sama dengan hari ini"). Model hanya berguna kalau konsisten lebih baik dari persistence.
- **Aktual vs prediksi:** sebar sampel 1.500 titik. Makin dekat ke garis putus-putus, makin tepat.
- **Sebaran galat:** histogram selisih prediksi dikurangi aktual.
- **Galat per provinsi dan per bulan:** batang tua menandai yang paling sulit diprediksi.
- **Evaluasi status EWS:** matriks konfusi tiga status beserta recall, precision, dan F1 per status. Recall status Tidak sehat paling penting untuk peringatan dini.
- **Perbandingan model (hasil tim):** tabel dari `model_metrics.csv`, nilai terbaik per kolom disorot.
- **Fitur yang paling dipakai model:** feature importance global dari `feature_importance.csv`. Ini menunjukkan apa yang diandalkan model, bukan penyebab polusi.
- Ada kotak **Arti istilah** untuk pembaca yang belum familiar dengan metrik.

### Tab Tren & episode
- Pilih tingkat (kabupaten/kota atau provinsi), daerahnya, dan **ambang polusi tinggi** (bawaan 55 µg/m³).
- Grafik PM2.5 aktual, prediksi, dan rata-rata 7 hari.
- Grafik selisih prediksi dan aktual.
- **Tabel episode polusi tinggi:** periode hari berturut-turut ketika PM2.5 aktual melewati ambang, lengkap dengan tanggal mulai, selesai, puncak, dan durasi.

### Tab Cuaca & musim
- **Heatmap korelasi** PM2.5 dengan suhu, kelembapan, curah hujan, kecepatan angin, tekanan udara, dan tutupan awan. Jika satu provinsi dipilih, barisnya adalah 15 kabupaten/kota berpenduduk terbanyak.
- **Sebar PM2.5 dan satu variabel cuaca** pilihan.
- **Rata-rata PM2.5 per bulan** untuk melihat musim polusi.

---

## 8. Data yang dibutuhkan

Dashboard mencari file di `data/data_gabungan/`. Jika tidak ada, dipakai data contoh di `dashboard/sample/` (jadi folder `dashboard` jangan dihapus).

| File | Isi | Dipakai di |
|---|---|---|
| `airguard_predictions.csv` | Prediksi dan nilai aktual harian per kabupaten/kota (`tanggal_prediksi`, `pm2_5_prediksi`, `pm2_5_aktual`, kota, provinsi) | EWS, Proyeksi (riwayat), Analitik |
| `airguard_preprocessed.csv` | Data harian PM2.5 dan cuaca (`tanggal`, `pm2_5`, suhu, kelembapan, curah hujan, angin, tekanan, awan) | Proyeksi musiman, tab Cuaca |
| `model_metrics.csv` | Perbandingan model (`model`, `MAE`, `RMSE`, `R2`) | Tab Evaluasi |
| `feature_importance.csv` | `feature`, `importance` | Tab Evaluasi |
| `airguard_forecast.csv` (opsional) | Proyeksi dari tim: `kota`, `provinsi`, `tanggal`, `pm2_5_prakiraan`, `batas_bawah`, `batas_atas` | Halaman Proyeksi |

Hal yang perlu diperhatikan tim data:
- **Sertakan kolom `kode_kabkota`** bila bisa. Pencocokan dengan daftar resmi (`referensi/kabkota_pulau_jawa.csv`) dilakukan lewat kode, lalu nama. Baris yang tidak cocok dibuang tanpa peringatan.
- Cakupan hanya kabupaten/kota Pulau Jawa. Wilayah di luar itu diabaikan.
- Nama kolom harus sama dengan file contoh di `dashboard/sample/`.
- Setelah mengganti file data, restart Streamlit.

## 9. Struktur file

```
dashboard_ews/
  app.py                  pintu masuk: landing lalu sidebar tiga halaman
  halaman_beranda.py      landing page
  halaman_ews.py          EWS harian H+1
  halaman_proyeksi.py     proyeksi jangka panjang
  halaman_analitik.py     analitik dan evaluasi
  data.py                 pembacaan data, status EWS, proyeksi musiman
  ui.py                   tema, CSS, komponen kartu
  logo.svg                logo sidebar
  referensi/              daftar resmi kabupaten/kota Pulau Jawa
  .streamlit/config.toml  tema warna
  requirements.txt
```

## 10. Keterbatasan yang perlu diketahui

- Semua angka masih sintetis sampai file asli tim masuk. Chip "Sumber: data contoh (sintetis)" di halaman Analitik akan hilang otomatis begitu file asli terbaca.
- Proyeksi saat ini berbasis pola musiman, bukan model machine learning.
- Ambang status (15 dan 55 µg/m³) mengikuti rincian proyek dan perlu diverifikasi ke regulasi.
- Rekomendasi di dashboard adalah ringkasan umum berdasarkan status PM2.5 dan bukan saran medis.
- Saat dideploy ke Streamlit Cloud, tema warna dibaca dari `.streamlit/config.toml` di akar repo, sehingga bisa berbeda dari tema di folder `dashboard_ews`. Warna widget sudah dikunci lewat CSS agar tampilannya tetap biru.
