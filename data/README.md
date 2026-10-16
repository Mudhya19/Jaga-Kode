# Modul Data JAGA-KODE

Direktori ini dirancang khusus untuk tata kelola data klaim, skema validasi, dan generator data sintetis dalam kepatuhan penuh terhadap **UU PDP No. 27/2022**.

## Struktur Subdirektori:
* **`raw/`**: Tempat penyimpanan data mentah dan tabel referensi standar medis:
  * Master Kamus Diagnosis (ICD-10)
  * Master Kamus Prosedur Medis (ICD-9-CM)
  * Master Tarif INA-CBG resmi (Permenkes No. 26/2021)
  * *Catatan*: Berkas mentah diabaikan oleh `.gitignore` untuk mencegah kebocoran data.
* **`processed/`**: Tempat penyimpanan dataset hasil rekayasa fitur (*feature engineered*), normalisasi z-score, dan pemisahan subset *train*, *validation*, dan *test*.
* **`schemas/`**: Skema kontrak data (*Data Contracts*), kamus data (*Data Dictionary*), dan definisi tipe data (misal: JSON Schema / Pydantic schema) untuk validasi format sebelum klaim diproses mesin AI.
* **`synthetic/`**: Modul dan skenario injeksi data klaim sintetis:
  * Kasus baseline normal (~85–90%)
  * Skenario anomali upcoding terkontrol (~10–15%): *ghost comorbidity*, eskalasi prosedur, *LoS inflation*, dan *unbundling*.
