# 02. Analisis Masalah dan Urgensi

## 1. Anatomi Upcoding dalam Ekosistem Klaim JKN

Dalam skema pembiayaan Jaminan Kesehatan Nasional (JKN) di Indonesia, pembayaran kepada Fasilitas Kesehatan Rujukan Tingkat Lanjut (FKRTL) menggunakan sistem tarif paket prospektif berbasis kelompok penyakit, yaitu **INA-CBG (*Indonesian Case Base Groups*)** yang diatur dalam Permenkes No. 26 Tahun 2021.

Tarif INA-CBG dihitung berdasarkan kombinasi variabel klinis dan administratif:
* **Diagnosis Utama (*Primary Diagnosis*)** menggunakan kodefikasi **ICD-10**.
* **Diagnosis Sekunder (*Secondary Diagnosis / Komorbiditas & Komplikasi*)** menggunakan **ICD-10**.
* **Prosedur / Tindakan Medis (*Surgical & Non-Surgical Procedures*)** menggunakan kodefikasi **ICD-9-CM**.
* **Tingkat Keparahan Kasus (*Severity Level*)**, terbagi atas:
  * Tingkat I : Kasus Ringan (*Sub-acute / without CC*)
  * Tingkat II : Kasus Sedang (*with Complication and/or Comorbidity - CC*)
  * Tingkat III: Kasus Berat (*with Major Complication and/or Comorbidity - MCC*)
* **Atribut Pelayanan Pendukung**: Lama rawat inap (*Length of Stay - LoS*), kelas rumah sakit (A, B, C, D), regionalisasi tarif, dan status keluar pasien (*discharge status*).

```
+-----------------------------------------------------------------------------+
|                               ANATOMI UPCODING                             |
|                                                                             |
|   +-------------------+       +--------------------+                        |
|   |   KONDISI RIIL    |       |   KLAIM DIAJUKAN   |                        |
|   |     PASIEN        |       |     (UPCODING)     |                        |
|   +-------------------+       +--------------------+                        |
|   | • Katarak Senilis | ----> | • Katarak + Komplikasi                      |
|   |   Ringan (LoS 1h) |       |   Kompleks (LoS 4h)                         |
|   | • Tindakan Standar|       | • Tindakan Spesialistik                     |
|   | • Severity Level I|       | • Severity Level III                        |
|   | • Nilai: Rp X     |       | • Nilai: Rp (X + Delta)                     |
|   +-------------------+       +--------------------+                        |
|                                         |                                   |
|   Inkonsistensi Tersembunyi:            v                                   |
|   [Diagnosis Ekstrem] <---> [Tindakan Biasa] <---> [LoS Janggal vs Peer]   |
+-----------------------------------------------------------------------------+
```

### Definisi dan Modus Upcoding
**Upcoding** adalah praktik manipulasi pengodean diagnosis dan/atau prosedur medis secara sengaja atau akibat kelalaian sistematis untuk menggeser kelompok INA-CBG ke tingkat tarif yang lebih tinggi daripada kondisi medis pasien yang sebenarnya. Modus umum meliputi:
1. **Penambahan Komorbiditas Semu (*Ghost Comorbidities*)**: Menambahkan diagnosis sekunder berbobot berat (misal: syok septik, gagal ginjal akut, asidosis metabolik berat) tanpa bukti rekaman medis, pemeriksaan laboratorium penunjang, atau terapi yang relevan.
2. **Eskalasi Prosedur (*Procedure Inflation*)**: Mengodekan tindakan bedah sederhana dengan kode tindakan bedah kompleks atau laparoskopi tingkat lanjut guna menaikkan kelompok tarif.
3. **Pemisahan Klaim (*Unbundling*)**: Memecah paket pelayanan tunggal menjadi beberapa tagihan terpisah yang tidak sah.
4. **Artifisial LoS (*Length of Stay Inflation*)**: Memperpanjang durasi rawat inap secara semu untuk menyesuaikan batas minimum keabsahan tingkat keparahan tinggi.

---

## 2. Bukti Empiris Mikro: Temuan Audit Klinis Kemenkes 2024

Urgensi penanganan upcoding bukan sekadar asumsi teoritis, melainkan didukung fakta lapangan. Pada tahun 2024, Kementerian Kesehatan Republik Indonesia bersama Badan Pengawasan Keuangan dan Pembangunan (BPKP) serta BPJS Kesehatan mempublikasikan temuan audit kepatuhan klaim pelayanan operasi katarak pada 3 Rumah Sakit swasta:

```
Hasil Audit Kasus Katarak (Kemenkes, 2024 - Sampel 3 RS):
============================================================
Total Berkas Diperiksa  : [|||||||||||||||||||||||||||||||||||||||] 39 Pasien
Sesuai Diagnosis Riil   : [||||||||||||||] 14 Pasien (35.9%)
Ketidaksesuaian/Anomali : [|||||||||||||||||||||] 25 Pasien (64.1%)
============================================================
```

> **Catatan Analitis:** Dari 39 sampel berkas yang diteliti secara mendalam, **hanya 14 pasien** yang terbukti memiliki indikasi klinis dan tindakan yang benar-benar sesuai dengan kode klaim yang ditagihkan. Sebanyak 25 klaim lainnya terindikasi mengalami manipulasi kode atau ketidaksesuaian rekam medis.  
> *Meskipun temuan ini merupakan studi kasus terarah dan tidak mencerminkan angka prevalensi nasional secara general, temuan ini menjadi bukti nyata bahwa berkas yang lolos verifikasi administratif formal kerap menyimpan manipulasi substansi klinis.*

---

## 3. Empat Kesenjangan Kritis Sistem Verifikasi Konvensional

Mengapa sistem verifikasi yang ada saat ini masih dapat ditembus oleh praktik upcoding? Tim SI DANDANG mengidentifikasi empat kesenjangan sistemik (*systemic gaps*):

### G1. Kesenjangan Skala (*Scale Gap*)
* **Masalah**: BPJS Kesehatan mengelola ratusan juta transaksi klaim per tahun dari ribuan FKRTL di seluruh Indonesia.
* **Dampak**: Jumlah personel verifikator sangat terbatas dibanding rasio volume berkas. Pemeriksaan manual mendalam (*deep-dive medical chart review*) terhadap setiap lembar resume medis mustahil dilakukan untuk 100% klaim.

### G2. Kesenjangan Kompleksitas Relasional (*Complexity Gap*)
* **Masalah**: Klaim upcoding modern disusun secara rapi secara administratif (*paperwork perfection*). Form terisi lengkap, tanda tangan dokter tersedia, dan kode terdaftar valid di kamus ICD.
* **Dampak**: Anomali upcoding hanya bisa terdeteksi jika pemeriksa menganalisis hubungan silang relasional:
  * Apakah tindakan bedah X lazim dilakukan pada diagnosis Y?
  * Apakah lama rawat inap 2 hari wajar untuk pasien dengan klaim keparahan Level III?
  * Apakah biaya obat dan alkes pendukung proporsional dengan komorbiditas yang diklaim?

### G3. Keterbatasan Aturan Statis (*Static Rule Rigidity*)
* **Masalah**: Mesin verifikasi saat ini didominasi oleh aturan deterministik berbasis logika `IF-THEN` (*rule-based engine*).
* **Dampak**: Aturan statis bersifat reaktif dan kaku. Pelaku upcoding yang mempelajari pola batas aturan (*threshold*) dapat dengan mudah melakukan manipulasi tepat di bawah batas deteksi (*threshold evasion*). Aturan statis juga gagal mengenali kombinasi anomali baru yang belum pernah dikodifikasikan secara manual.

### G4. Kesenjangan Keterjelasan & Kelelahan Peringatan (*Black-box Alert Fatigue*)
* **Masalah**: Beberapa inisiatif analitik terdahulu menggunakan model prediktif berbasis *machine learning* tertutup (*black-box*) yang hanya mengeluarkan skor risiko angka (misalnya: `Risk Score: 0.91`).
* **Dampak**: Tanpa penjelasan rinci tentang alasan mengapa klaim tersebut berbahaya, verifikator bingung harus mulai mencari anomali di bagian mana. Hal ini menciptakan kelelahan peringatan (*alert fatigue*), di mana verifikator akhirnya mengabaikan sinyal AI atau menghabiskan waktu terlalu lama untuk membuktikan peringatan tersebut.

---

## 4. Rumusan Masalah & Sasaran Solusi

Berdasarkan kesenjangan di atas, rumusan masalah utama yang dijawab oleh **JAGA-KODE** adalah:

> *"Bagaimana merancang sistem pendukung keputusan bagi verifikator BPJS Kesehatan yang mampu mendeteksi, menjelaskan, dan memprioritaskan klaim berisiko upcoding secara presisi dan adaptif, tanpa menghilangkan kendali manusia (Human-in-the-Loop) dan tanpa melakukan penolakan klaim sepihak secara otomatis?"*

### Kebutuhan Solusi Ideal:
1. **Penyaringan Presisi**: Memisahkan klaim wajar dari klaim beranomali sebelum masuk meja verifikator.
2. **Konteks Komparatif (*Peer Grouping*)**: Menilai kewajaran klaim suatu RS berdasarkan distribusi statistik rumah sakit sekelas, bukan dipukul rata.
3. **Kartu Penjelasan Transparan**: Menerjemahkan indikasi teknis AI ke dalam narasi klinis yang siap ditindaklanjuti.
4. **Efisiensi Alokasi Waktu**: Memastikan energi verifikator difokuskan pada klaim dengan potensi kebocoran dana terbesar.
