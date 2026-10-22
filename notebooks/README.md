# Jupyter Notebooks Eksperimen & Pemodelan Data

Direktori `notebooks/` digunakan untuk eksplorasi data klaim FKRTL BPJS Kesehatan, pemrofilan *Peer Group*, kalibrasi aturan klinis Permenkes No. 26/2021, pelatihan model deteksi anomali, serta evaluasi metrik sistem **JAGA-KODE**.

## Daftar Notebook Utama:

1. **[`jaga_kode_dual_guardrail_modeling.ipynb`](jaga_kode_dual_guardrail_modeling.ipynb)**:
   * Eksplorasi dan pemisahan populasi klaim Rawat Inap Tingkat Lanjut (RITL — 195.544 klaim) dari keseluruhan 1.699.219 klaim FKRTL.
   * Pemrofilan statistik *Peer Group* lintas kelas rumah sakit, kepemilikan, regional tarif, dan kelompok *Casemix Main Group* (CMG) dengan *Empirical Bayes Shrinkage*.
   * Evaluasi deterministik 5 aturan klinis Permenkes No. 26/2021 (*Consistency Guardrail*) murni dari sinyal pra-verifikasi.
   * Pelatihan model *Peer-Group Isolation Forest* multivariat serta komparasi terhadap model *baseline* (*Univariate Z-Score* dan *Local Outlier Factor*).
   * Fusi skor *Composite Priority Score* (CPS), *5-Axis Explainable Anomaly Radar* (XAI), serta pengujian *Controlled Upcoding Test Bench* (`SCN-01` s.d. `SCN-04`).
