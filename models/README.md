# Modul Penyimpanan Model & Artefak Serialisasi

Direktori `models/` dirancang untuk mengelola artefak serialisasi model kecerdasan buatan, pipeline transformasi data, dan model pembanding (*baselines*).

## Rancangan Struktur:

* **`models/core/`**:
  * Serialisasi bobot dan estimator utama:
    * Model *Isolation Forest* terlatih (`isolation_forest.joblib`)
    * Objek *StandardScaler* / *RobustScaler* untuk normalisasi fitur tabular
    * Matriks probabilitas ko-okurensi diagnosis-tindakan
    * Matriks bobot aturan *Consistency Guardrail*
* **`models/baselines/`**:
  * Model pembanding untuk benchmark eksperimen data science (misal: Logistic Regression, Random Forest, K-Means clustering, atau LOF).
  * Catatan: Semua artefak binary model diabaikan oleh `.gitignore` dan dikelola menggunakan versioning terstruktur.
