# Jupyter Notebooks Eksperimen & Analisis Data

Direktori `notebooks/` digunakan untuk fase eksplorasi data (*Exploratory Data Analysis*), prototipe algoritma cepat, kalibrasi ambang batas, dan visualisasi hasil riset tim Data Science (Muhammad Dhiauddin).

## Rencana Urutan Notebook Riset:

1. **`01_exploratory_data_analysis.ipynb`**:
   * Eksplorasi distribusi fitur data klaim sintetis.
   * Analisis variansi *Length of Stay* (LoS) dan biaya per kelas faskes.
2. **`02_guardrail_rule_prototyping.ipynb`**:
   * Pengujian logika aturan klinis deterministik (*hard checks* dan relasi diagnosis-tindakan).
3. **`03_anomaly_engine_experiments.ipynb`**:
   * Eksperimen pelatihan *Isolation Forest*, tuning parameter contamination, dan evaluasi *Peer Grouping*.
4. **`04_risk_fusion_and_xai_radar.ipynb`**:
   * Kalibrasi pembobotan sinyal risiko ($\alpha$) dan visualisasi radar Explanation Card.
5. **`05_benchmark_and_evaluation.ipynb`**:
   * Pengujian metrik Precision@K, Review Yield, dan kurva PR-AUC pada skenario injeksi upcoding.
