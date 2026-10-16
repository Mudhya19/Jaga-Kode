# 04. Spesifikasi Data dan Rekayasa Fitur

## 1. Kebijakan Data dan Kerangka Data Sintetis (*Synthetic Data Framework*)

Sesuai dengan ketentuan panduan peserta (*Participant Guide*) Healthkathon BPJS Kesehatan 2026 dan Undang-Undang No. 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP):
> **Data peserta JKN riil tidak boleh digunakan, diakses, diolah, atau disebarluaskan tanpa izin tertulis resmi dari otoritas terkait.**

Untuk itu, tahap pengembangan dan pengujian prototipe JAGA-KODE dibangun menggunakan **Data Sintetis Tabular (*Synthetic Tabular Data*)** yang dirancang mencerminkan karakteristik statistik dan kaidah klinis pembiayaan INA-CBG di Indonesia.

```
+---------------------------------------------------------------------------------+
|                       PIPELINE GENERASI DATA SINTETIS                          |
|                                                                                 |
|  [Distribusi Empiris INA-CBG]      [Standar Koding ICD-10 & ICD-9-CM]           |
|                │                                   │                            |
|                └─────────────────┬─────────────────┘                            |
|                                  ▼                                              |
|            [Generator Data Sintetis Berbasis Probabilitas]                      |
|                                  │                                              |
|         ┌────────────────────────┴────────────────────────┐                     |
|         ▼                                                 ▼                     |
|  [Kasus Normal (~85-90%)]                  [Kasus Anomali Upcoding (~10-15%)]   |
|  - Diagnosis, tindakan, & LoS konsisten    - Eskalasi Severity Level semu       |
|  - Biaya proporsional dengan kelas RS      - Tambahan komorbiditas palsu        |
|  - Sesuai kaidah INA-CBG                   - LoS melampaui batas kewajaran      |
+---------------------------------------------------------------------------------+
```

---

## 2. Kamus Data Tabular (*Data Dictionary*)

Skema data klaim tabular yang diproses oleh sistem JAGA-KODE mencakup variabel-variabel kunci berikut:

| Nama Variabel | Tipe Data | Deskripsi & Format | Contoh Nilai | Peran dalam Model |
|---|---|---|---|---|
| `claim_id` | String | Pengidentifikasi unik klaim | `KLM-2026-00412` | ID Pelacak |
| `patient_pseudo_id` | String | ID tersamarkan peserta (*pseudonym*) | `PST-99812-X` | Pelindung privasi |
| `faskes_id` | String | ID tersamarkan fasilitas kesehatan | `FASKES-RS-042` | Pengelompokan peer |
| `faskes_class` | Category | Kelas rumah sakit rujukan | `A`, `B`, `C`, `D` | Pembentuk *Peer Group* |
| `faskes_type` | Category | Jenis kepemilikan/tipe faskes | `Pemerintah`, `Swasta`, `Khusus` | Pembentuk *Peer Group* |
| `region_code` | Integer | Kode regionalisasi tarif BPJS | `1`, `2`, `3`, `4`, `5` | Penyesuaian tarif |
| `icd10_primary` | String | Kode diagnosis utama penyakit | `H25.0` (Katarak senilis) | Fitur klinis dasar |
| `icd10_secondary` | List[Str] | Daftar diagnosis sekunder/komplikasi | `["I10", "E11.9"]` | Analisis komorbiditas |
| `icd9_procedures` | List[Str] | Daftar kode prosedur/tindakan medis | `["13.41", "89.52"]` | Analisis tindakan |
| `los_days` | Integer | Durasi rawat inap (*Length of Stay*) | `2` (hari) | Deteksi deviasi durasi |
| `severity_level` | Integer | Tingkat keparahan kasus INA-CBG | `1` (I), `2` (II), `3` (III) | Deteksi eskalasi tarif |
| `inacbg_code` | String | Kode paket kelompok INA-CBG | `H-4-10-I` | Validasi tarif |
| `claim_amount` | Float | Nilai klaim diajukan (Rupiah) | `8500000.00` | Deteksi anomali biaya |
| `hospital_cost` | Float | Biaya riil yang dikeluarkan RS | `7800000.00` | Rasio biaya operasional |
| `discharge_status` | Category | Status keluar pasien | `Sembuh`, `Rujuk`, `Meninggal` | Kontrol keparahan |

---

## 3. Rekayasa Fitur Tingkat Lanjut (*Feature Engineering*)

Data mentah ditransformasikan menjadi representasi fitur relasional berdaya diskriminasi tinggi guna mendeteksi manipulasi upcoding:

```
[Data Mentah Klaim] ────► [Transformasi Rekayasa Fitur] ────► [Fitur Siap Model AI]
  - icd10_primary           - procedure_diag_plausibility       - Vektor Multivariat
  - icd9_procedures         - los_peer_zscore                   - Matriks Relasi
  - los_days                - severity_cost_ratio               - Deviasi Statistik
  - faskes_class            - comorbidity_complexity_score      - Bobot Aturan
```

### 1. Indeks Kelayakan Diagnosis-Tindakan (*Procedure-Diagnosis Plausibility Index*)
* **Konsep**: Menghitung probabilitas keterkaitan tindakan medis $P$ terhadap diagnosis utama $D$.
* **Formulasi**: Berdasarkan matriks co-occurrence klinis $M(D, P)$:
  $$Score_{plausibility} = \frac{\text{Frekuensi}(D, P)}{\sum_{P'} \text{Frekuensi}(D, P')}$$
* **Indikasi Upcoding**: Nilai $Score_{plausibility} \approx 0$ mengindikasikan tindakan medis tidak memiliki relevansi klinis terhadap diagnosis yang diajukan.

### 2. Deviasi Lama Rawat Terhadap Peer Group (*LoS Peer Z-Score & Percentile*)
* **Konsep**: Membandingkan lama rawat klaim dengan distribusi kasus serupa pada rumah sakit di kelas yang setara.
* **Formulasi**:
  $$Z_{LoS} = \frac{LoS - \mu_{\text{peer}(D, \text{class})}}{\sigma_{\text{peer}(D, \text{class})}}$$
  $$Percentile_{LoS} = F(LoS \mid D, \text{class})$$
* **Indikasi Upcoding**: $Percentile_{LoS} > 95\%$ pada kasus ber-severity level rendah menunjukkan indikasi penahanan pasien yang tidak perlu atau manipulasi pencatatan rawat inap.

### 3. Rasio Keparahan terhadap Biaya (*Cost-to-Severity Disparity Ratio*)
* **Konsep**: Menguji apakah klaim dengan *Severity Level III* (kasus berat berbiaya tinggi) didukung oleh biaya riil operasional yang proporsional.
* **Formulasi**:
  $$R_{cost} = \frac{\text{claim\_amount}}{\text{hospital\_cost}}$$
* **Indikasi Upcoding**: Nilai rasio $R_{cost}$ yang melambung tinggi secara ekstrem pada Severity Level III (misal selisih tarif paket jauh melampaui biaya riil karena tidak ada tindakan intensif/obat mahal yang benar-benar diberikan) mengindikasikan *phantom severity*.

### 4. Skor Kompleksitas Komorbiditas (*Comorbidity Severity Index - CSI*)
* **Konsep**: Menilai apakah daftar diagnosis sekunder yang diajukan benar-benar memenuhi kriteria komplikasi mayor (*Major Complication/Comorbidity - MCC*) yang diakui INA-CBG atau sekadar akumulasi kode minor yang sengaja ditumpuk.
* **Formulasi**:
  $$CSI = \sum_{c \in \text{secondary}} Weight_{\text{INA-CBG}}(c)$$

---

## 4. Pembentukan Kelompok Pembanding (*Peer Grouping Clustering*)

Untuk mencegah bias yang tidak adil terhadap rumah sakit rujukan dengan spesialisasi tinggi, pembentukan *Peer Group* dilakukan melalui segmentasi multi-dimensi:

```
                                 [SEMUA FASKES]
                                       │
                  ┌────────────────────┴────────────────────┐
                  ▼                                         ▼
         [Rumah Sakit Umum]                       [Rumah Sakit Khusus]
          (Kelas A, B, C, D)                    (Mata, Jantung, Kanker)
                  │                                         │
       ┌──────────┴──────────┐                              │
       ▼                     ▼                              ▼
 [Regional Jawa]     [Regional Luar Jawa]              [Sub-Spesialis]
```

Atribut Pengelompokan:
1. **Kelas Faskes**: Kelas A (Pusat Rujukan Nasional/Provinsi), Kelas B (Rujukan Regional), Kelas C (Kabupaten/Kota), Kelas D (Pratama).
2. **Karakteristik Layanan**: Rumah Sakit Umum vs Rumah Sakit Khusus (misal: RS Khusus Mata memiliki pola koding katarak yang sangat berbeda dari RSU).
3. **Zona Regionalisasi**: Menyesuaikan bobot tarif INA-CBG yang bervariasi antar-wilayah geografis di Indonesia.
