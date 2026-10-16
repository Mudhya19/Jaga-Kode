# 07. Peta Jalan dan Manajemen Proyek

## 1. Peta Jalan Eksekusi 6 Fase (*6-Phase Execution Roadmap*)

Pengembangan JAGA-KODE dirancang secara terstruktur dan modular dalam 6 fase eksekusi menuju prototipe fungsional yang siap didemonstrasikan dalam ajang Healthkathon BPJS Kesehatan 2026:

```
[FASE 1: Finalisasi Kebutuhan]
  • Pemetaan user flow verifikator BPJS
  • Spesifikasi fitur utama & perumusan backlog sistem
         │
         ▼
[FASE 2: Persiapan Data & Skema]
  • Pembuatan data dictionary skema klaim tabular
  • Skenario pengujian & pipeline awal data dummy/sintetis
         │
         ▼
[FASE 3: Pengembangan Analitik & AI]
  • Pembangunan Consistency Guardrail (Rule Engine)
  • Pelatihan Anomaly Engine (Isolation Forest & Peer Grouping)
  • Perhitungan Risk Fusion & logika Explainable AI
         │
         ▼
[FASE 4: Pengembangan Web & Antarmuka]
  • Desain & coding antarmuka dashboard responsif
  • Integrasi REST API backend & visualisasi XAI radar
  • Workspace antrean prioritas ulasan klaim
         │
         ▼
[FASE 5: Integrasi & Pengujian Internal]
  • Uji coba end-to-end secara internal pada dataset uji
  • Produksi tangkapan layar (screenshot) & video demonstrasi
  • Pengukuran metrik operasional awal (Precision@K, Review Yield)
         │
         ▼
[FASE 6: Penyempurnaan & Peta Pilot]
  • Evaluasi fungsionalitas berdasarkan masukan penguji
  • Persiapan dokumen arsitektur untuk potensi program percontohan (pilot)
    menggunakan data berizin resmi di ekosistem JKN
```

---

## 2. Profil dan Komposisi Keahlian Tim SI DANDANG

Tim SI DANDANG terdiri atas tiga talenta dengan kompetensi yang saling melengkapi (*cross-functional complementary skills*):

```
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│       MUHAMMAD DHIAUDDIN        │      MUHAMMAD ALISYAHBANA       │      MUHAMMAD ALI MAULANA       │
│   Ketua Tim - Data Scientist    │     Anggota - Web Developer     │     Anggota - System Analyst    │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│ • Pipeline data & rekayasa fitur│ • Arsitektur backend & REST API │ • Analisis kebutuhan bisnis     │
│ • Model Isolation Forest        │ • Antarmuka web responsif       │ • Pemetaan SOP verifikator BPJS │
│ • Logika Explainable AI (XAI)   │ • Visualisasi radar XAI         │ • Desain alur Human-in-the-Loop │
│ • Evaluasi metrik Precision@K   │ • Integrasi model analitik      │ • Dokumentasi teknis & kepatuhan│
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│ Kontak:                         │ Kontak:                         │ Kontak:                         │
│ muhammamddhiauddin40@gmail.com  │ malisyahbana5@gmail.com         │ alimaulana0208@gmail.com        │
│ 085652203518                    │ 085346184066                    │ 087811201379                    │
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

### Matriks Tanggung Jawab Tim (RACI Matrix)

| Modul / Komponen Proyek | M. Dhiauddin (DS) | M. Alisyahbana (Dev) | M. Ali Maulana (SA) |
|---|---|---|---|
| Perumusan Masalah & Alur Verifikasi | Consulted | Informed | **Accountable / Responsible** |
| Spesifikasi Skema Data & Kasus Uji | **Responsible** | Consulted | Accountable |
| Mesin Deteksi Ganda (Rule + Anomaly) | **Accountable / Responsible** | Consulted | Informed |
| Logika Risk Fusion & XAI Radar | **Responsible** | Support | Consulted |
| Backend API & Layanan Integrasi | Consulted | **Accountable / Responsible** | Informed |
| Frontend Workspace & UI Dashboard | Informed | **Accountable / Responsible** | Consulted |
| Pengujian Skenario & Evaluasi Metrik | **Accountable / Responsible** | Support | Support |
| Dokumentasi & Proposal Kompetisi | Support | Support | **Accountable / Responsible** |

*Keterangan: R = Responsible, A = Accountable, C = Consulted, I = Informed.*

---

## 3. Analisis Kelayakan Proyek (*Feasibility Analysis*)

Pengembangan JAGA-KODE memiliki tingkat kelayakan teknis dan operasional yang sangat tinggi karena:
1. **Ruang Lingkup Terfokus (*Scoped & Targeted*)**: Sistem secara spesifik membidik satu subkategori kritis (*Upcoding* pada FKRTL), sehingga energi tim terkonsentrasi penuh tanpa disrupsi fitur sekunder.
2. **Kemandirian Infrastruktur (*Self-Contained*)**: Selama kompetisi, sistem tidak bergantung pada integrasi langsung ke sistem produksi BPJS Kesehatan (*VClaim* / *SIM-KARS*), melainkan memanfaatkan simulasi API lokal dengan data sintetis.
3. **Teknologi Efisien & Andal**: Memanfaatkan ekosistem teknologi yang matang:
   * **Analitik / Data Science**: Python (Scikit-Learn, Pandas, NumPy)
   * **Backend / API**: FastAPI / Flask yang ringan dan berkinerja tinggi
   * **Frontend / UI**: Modern Web UI (React / Tailwind atau Streamlit/Next.js)
   * **Penyimpanan**: PostgreSQL / SQLite terenkripsi

---

## 4. Matriks Manajemen dan Mitigasi Risiko Proyek

| Kategori Risiko | Deskripsi Potensi Kendala | Tingkat Risiko | Rencana Mitigasi Proaktif |
|---|---|:---:|---|
| **Teknis: Data Imbalance** | Kasus anomali sintetis terlalu sedikit sehingga model gagal mempelajari pola pemisah. | Sedang | Menerapkan teknik *Controlled Anomaly Injection* dan pembobotan *sample weight* saat pelatihan. |
| **Teknis: Latensi Antarmuka** | Visualisasi radar XAI lambat dimuat saat menampilkan antrean klaim dalam jumlah besar. | Rendah | Menggunakan *asynchronous batch pre-computation* untuk skor risiko sebelum ditampilkan di frontend. |
| **Operasional: Resistensi Pengguna** | Verifikator merasa terbebani jika tampilan sistem rumit atau menambah birokrasi koding. | Tinggi | Desain antarmuka *Verification Workspace* dibuat minimalis, meniru tata letak familiar form verifikasi BPJS, dan fokus pada satu klik tindakan (*one-click action*). |
| **Kepatuhan: Pelanggaran Privasi Data** | Potensi tuduhan penggunaan data peserta JKN tanpa izin. | Sangat Tinggi | Komitmen tegas menggunakan 100% data dummy sintetis; tidak ada data riil yang disimpan di repositori. |

---

## 5. Referensi Regulasi dan Sumber Daya Resmi

Dokumentasi ini mengacu pada landasan hukum dan sumber daya resmi berikut:
1. **Portal Resmi Healthkathon BPJS Kesehatan**:  
   [https://healthkathon.bpjs-kesehatan.go.id/](https://healthkathon.bpjs-kesehatan.go.id/)
2. **Undang-Undang Republik Indonesia Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi**:  
   [https://peraturan.bpk.go.id/Details/229798/uu-no-27-tahun-2022](https://peraturan.bpk.go.id/Details/229798/uu-no-27-tahun-2022)
3. **Peraturan Menteri Kesehatan Republik Indonesia Nomor 16 Tahun 2019 tentang Pencegahan dan Penanganan Kecurangan (Fraud) serta Pengenaan Sanksi Administrasi terhadap Kecurangan (Fraud) dalam Pelaksanaan Program Jaminan Kesehatan**:  
   [https://peraturan.bpk.go.id/Details/122606/permenkes-no-16-tahun-2019](https://peraturan.bpk.go.id/Details/122606/permenkes-no-16-tahun-2019)
4. **Peraturan Menteri Kesehatan Republik Indonesia Nomor 26 Tahun 2021 tentang Pedoman Indonesian Case Base Groups (INA-CBG) dalam Penyelenggaraan Program Jaminan Kesehatan**:  
   [https://peraturan.bpk.go.id/Details/180223/permenkes-no-26-tahun-2021](https://peraturan.bpk.go.id/Details/180223/permenkes-no-26-tahun-2021)
