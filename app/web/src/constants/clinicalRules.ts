/**
 * Katalog Aturan Konsistensi Klinis Permenkes No. 26/2021 & Template Catatan SOP
 */

export interface ClinicalRuleItem {
  code: string;
  title: string;
  regulation: string;
  weight: number;
  summary: string;
}

export const PERMENKES_RULES_CATALOG: ClinicalRuleItem[] = [
  {
    code: 'RULE_GHOST_COMORBIDITY',
    title: 'Ghost Comorbidity (Komorbiditas Semu)',
    regulation: 'Permenkes No. 26/2021 — Kaidah Koding Diagnosis Sekunder & Sumber Daya',
    weight: 35,
    summary:
      'Klaim Severity Level II/III pada rawat inap singkat (≤1 hari) dengan status pulang sembuh namun mencantumkan komorbiditas mayor/multipel tanpa bukti terapi intensif.',
  },
  {
    code: 'RULE_SEVERITY_JUMP',
    title: 'Unjustified Severity Jump (Lonjakan Severity III)',
    regulation: 'Permenkes No. 26/2021 — Validasi Major Complication & Comorbidity (MCC)',
    weight: 30,
    summary:
      'Klaim naik ke tingkat keparahan tertinggi (Severity III) dengan rasio biaya >1.8x median kelompok faskes sebaya tanpa diagnosis komorbiditas mayor (MCC).',
  },
  {
    code: 'RULE_LOS_INFLATION',
    title: 'Length of Stay (LoS) Inflation',
    regulation: 'Permenkes No. 16/2019 — Pencegahan Perpanjangan Hari Rawat Tanpa Indikasi',
    weight: 25,
    summary:
      'Durasi rawat inap melampaui >3.0 Standar Deviasi (Z-Score) di atas rata-rata kelompok faskes sejenis (Peer Group × CMG).',
  },
  {
    code: 'RULE_PROCEDURE_DIAGNOSIS_CONFLICT',
    title: 'Procedure–Diagnosis Coherence Conflict',
    regulation: 'Permenkes No. 26/2021 — Kesesuaian Klinis ICD-10 & Prosedur INA-CBG',
    weight: 30,
    summary:
      'Probabilitas ko-okurensi empiris antara Diagnosis Primer (FKL17A), Jenis Prosedur (FKL21), dan Severity sangat rendah (<1.5%).',
  },
  {
    code: 'RULE_SPECIAL_CMG_UNBUNDLING',
    title: 'Special CMG & Tariff Unbundling',
    regulation: 'Permenkes No. 26/2021 — Paket Tarif Tunggal INA-CBG & Top-Up Special CMG',
    weight: 25,
    summary:
      'Indikasi klaim top-up Special CMG (FKL33) atau kelebihan tagihan rumah sakit (FKL47) >15% di atas acuan paket INA-CBG pada rawat singkat.',
  },
];

export const QUICK_NOTE_TEMPLATES: Record<string, string[]> = {
  REJECTED_UPCODING: [
    'Koreksi downcode ke Severity Level I sesuai Permenkes 26/2021: pasien rawat 1 hari pulang sehat tanpa bukti terapi komorbiditas mayor (N17/I50/A41) pada resume medis.',
    'Tolak eskalasi Severity III: tidak ditemukan bukti intervensi ICU/HD maupun penunjang laboratorium yang mendukung komplikasi berat.',
  ],
  PENDING_CLARIFICATION: [
    'Tunda klaim untuk klarifikasi Faskes: mohon lampirkan resume medis lengkap, hasil laboratorium penunjang, dan lembar observasi harian terkait durasi rawat inap.',
    'Konfirmasi rincian tagihan Special CMG (FKL33) dan kesesuaian kode tindakan prosedur utama dengan laporan operasi.',
  ],
  APPROVED: [
    'Klaim disetujui: kode diagnosis primer ICD-10, kode INA-CBG, lama rawat inap, dan rincian biaya telah sesuai dengan bukti rekam medis serta standar Peer Group.',
    'Deviasi biaya terkonfirmasi valid berdasarkan rujukan kasus kompleks tersier disertai bukti penunjang medis lengkap.',
  ],
};
