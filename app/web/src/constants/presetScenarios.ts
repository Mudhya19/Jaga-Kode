/**
 * Skenario Demo Preset & Fallback Evaluated Claims untuk JAGA-KODE
 */

import type {
  ClaimEvaluationResponse,
  PresetCaseKey,
  RiskCategory,
} from '../types/jagaKode';

export interface PresetScenarioMeta {
  key: PresetCaseKey;
  title: string;
  subtitle: string;
  badge: string;
  expectedTier: RiskCategory;
  description: string;
}

export const PRESET_SCENARIOS: PresetScenarioMeta[] = [
  {
    key: 'clean_normal',
    title: '1. Klaim Wajar (Normal)',
    subtitle: 'Hipertensi I10 • Sev I • LoS 3 Hari',
    badge: 'LOW RISK',
    expectedTier: 'LOW_RISK',
    description: 'Klaim proporsional sesuai median Peer Group RS Tipe C. Lolos Fast-Track otomatis.',
  },
  {
    key: 'ghost_comorbidity',
    title: '2. Ghost Comorbidity',
    subtitle: 'I10 + N17.9, I50.9, A41.9 • LoS 1 Hr Sehat',
    badge: 'HIGH RISK',
    expectedTier: 'HIGH_RISK',
    description:
      'Klaim Severity III dengan gagal ginjal akut, gagal jantung & sepsis namun rawat inap 1 hari pulang sehat.',
  },
  {
    key: 'severity_jump',
    title: '3. Severity Escalation',
    subtitle: 'Diabetes E11 • Sev III Tanpa MCC • 2.9x Tarif',
    badge: 'HIGH RISK',
    expectedTier: 'HIGH_RISK',
    description:
      'Lonjakan klaim ke Severity Level III dengan biaya Rp 14,8 Jt tanpa komorbiditas mayor yang memadai.',
  },
  {
    key: 'los_inflation',
    title: '4. LoS Inflation',
    subtitle: 'Pneumonia J18 • Rawat 15 Hari (Z > +3 SD)',
    badge: 'HIGH RISK',
    expectedTier: 'HIGH_RISK',
    description:
      'Perpanjangan lama rawat inap ekstrem (15 hari) melampaui 3 standar deviasi rata-rata Peer Group.',
  },
  {
    key: 'unbundling',
    title: '5. Special CMG Unbundling',
    subtitle: 'CAD I25 • Top-Up FKL33 Rp 4,5 Jt • Tagihan Rp 15,8 Jt',
    badge: 'MEDIUM RISK',
    expectedTier: 'MEDIUM_RISK',
    description:
      'Klaim add-on Special CMG & pemecahan paket tarif di atas batas kewajaran tarif dasar INA-CBG.',
  },
];

export const HUMAN_DECISIONS = new Set<string>([
  'APPROVED',
  'PENDING_CLARIFICATION',
  'PENDING_VERIFICATION',
  'REJECTED_UPCODING',
]);

export function estimateClaimDisputeIdr(claim: ClaimEvaluationResponse): number {
  if (claim.risk_category === 'LOW_RISK') return 0;
  const billed = claim.FKL47 ?? 0;
  const standard = claim.FKL32 && claim.FKL32 > 0 ? claim.FKL32 : billed;
  const directDiff = Math.max(0, billed - standard);
  const ratio = claim.cost_peer_ratio ?? 1;
  const peerDiff = ratio > 1.05 && billed > 0 ? Math.max(0, billed - billed / ratio) : 0;
  return Math.round(Math.max(directDiff, peerDiff));
}

export function buildFallbackEvaluatedClaims(): ClaimEvaluationResponse[] {
  return [
    {
      claim_id: 'CLM-DEMO-GHOST',
      risk_index: 76.2,
      risk_category: 'HIGH_RISK',
      badge_color: '#ef4444',
      primary_driver: 'Pelanggaran Regulasi Permenkes',
      recommended_action:
        'Prioritas Audit Klinis: Cek Bukti Penunjang Komorbiditas & Kesesuaian Tindakan pada Resume Medis',
      rule_risk_score: 60.0,
      ml_anomaly_score: 96.0,
      rule_violations: ['RULE_GHOST_COMORBIDITY', 'RULE_SPECIAL_CMG_UNBUNDLING'],
      radar: {
        los_deviation: 80.0,
        cost_deviation: 92.4,
        comorbidity_intensity: 90.0,
        severity_level: 95.0,
        regulatory_violation: 85.0,
      },
      clinical_narrative: [
        'Klaim Tingkat Keparahan Level 3 diajukan dengan durasi rawat sangat singkat (1 hari).',
        'Biaya tagih mencapai 2.66x median kelompok faskes sebaya pada CMG yang sama.',
        'Terpicu aturan Consistency Guardrail: GHOST COMORBIDITY, SPECIAL CMG UNBUNDLING.',
      ],
      explanation_text:
        'Klaim Tingkat Keparahan Level 3 diajukan dengan durasi rawat sangat singkat (1 hari). Biaya tagih mencapai 2.66x median kelompok faskes sebaya.',
      cost_peer_ratio: 2.66,
      los_peer_zscore: -0.65,
      comorbidity_count: 3,
      has_severe_comorbidity: 1,
      FKL07: 4,
      FKL08: 1,
      FKL09: 3,
      FKL10: 2,
      FKL14: 1,
      FKL15A: 'I10',
      FKL17A: 'I10',
      FKL18: 'I10.0',
      FKL19: 'I-4-17-III',
      FKL20: 9,
      FKL21: 4,
      FKL23: 3,
      severity_level: 3,
      FKL31: 1,
      FKL32: 4500000,
      FKL33: 0,
      FKL47: 9800000,
      los: 1,
      peer_group_id: '4_1_3_1',
      secondary_diagnoses: ['N17.9', 'I50.9', 'A41.9'],
    },
    {
      claim_id: 'CLM-DEMO-SEV-JUMP',
      risk_index: 67.8,
      risk_category: 'HIGH_RISK',
      badge_color: '#ef4444',
      primary_driver: 'Tingkat Keparahan (Severity)',
      recommended_action:
        'Prioritas Audit Klinis: Validasi Komorbiditas Mayor (MCC) untuk Klaim Severity Level III',
      rule_risk_score: 55.0,
      ml_anomaly_score: 83.4,
      rule_violations: ['RULE_SEVERITY_JUMP', 'RULE_SPECIAL_CMG_UNBUNDLING'],
      radar: {
        los_deviation: 42.0,
        cost_deviation: 88.5,
        comorbidity_intensity: 60.0,
        severity_level: 92.0,
        regulatory_violation: 75.0,
      },
      clinical_narrative: [
        'Biaya tagih mencapai 2.90x median kelompok faskes sebaya pada CMG yang sama.',
        'Terdapat 3 diagnosis sekunder minor tanpa komorbiditas mayor terverifikasi (indikasi Ghost Comorbidity).',
        'Terpicu aturan Consistency Guardrail: SEVERITY JUMP, SPECIAL CMG UNBUNDLING.',
      ],
      explanation_text:
        'Lonjakan klaim ke Severity III dengan rasio biaya 2.90x median peer group tanpa komorbiditas mayor.',
      cost_peer_ratio: 2.9,
      los_peer_zscore: -0.35,
      comorbidity_count: 3,
      has_severe_comorbidity: 0,
      FKL07: 2,
      FKL08: 1,
      FKL09: 2,
      FKL10: 2,
      FKL14: 1,
      FKL15A: 'E11',
      FKL17A: 'E11',
      FKL18: 'E11.9',
      FKL19: 'E-4-10-III',
      FKL20: 5,
      FKL21: 4,
      FKL23: 3,
      severity_level: 3,
      FKL31: 1,
      FKL32: 5100000,
      FKL33: 0,
      FKL47: 14800000,
      los: 2,
      peer_group_id: '2_1_2_1',
      secondary_diagnoses: ['Z00.0', 'E11.0', 'R51'],
    },
    {
      claim_id: 'CLM-DEMO-LOS-INFL',
      risk_index: 71.6,
      risk_category: 'HIGH_RISK',
      badge_color: '#ef4444',
      primary_driver: 'Deviasi Hari Rawat (LoS)',
      recommended_action:
        'Prioritas Audit Klinis: Konfirmasi Indikasi Medis Perpanjangan Hari Rawat Inap (>3 SD Peer Group)',
      rule_risk_score: 50.0,
      ml_anomaly_score: 86.0,
      rule_violations: ['RULE_LOS_INFLATION', 'RULE_SPECIAL_CMG_UNBUNDLING'],
      radar: {
        los_deviation: 95.0,
        cost_deviation: 82.0,
        comorbidity_intensity: 15.0,
        severity_level: 30.0,
        regulatory_violation: 70.0,
      },
      clinical_narrative: [
        'Durasi rawat inap (15 hari) melampaui rata-rata kelompok faskes sebaya (Z-Score: +3.42).',
        'Terpicu aturan Consistency Guardrail: LOS INFLATION.',
      ],
      explanation_text:
        'Durasi rawat inap 15 hari melampaui 3 standar deviasi rata-rata Peer Group.',
      cost_peer_ratio: 2.35,
      los_peer_zscore: 3.42,
      comorbidity_count: 0,
      has_severe_comorbidity: 0,
      FKL07: 4,
      FKL08: 1,
      FKL09: 3,
      FKL10: 2,
      FKL14: 1,
      FKL15A: 'J18',
      FKL17A: 'J18',
      FKL18: 'J18.9',
      FKL19: 'J-4-16-I',
      FKL20: 10,
      FKL21: 4,
      FKL23: 1,
      severity_level: 1,
      FKL31: 1,
      FKL32: 4000000,
      FKL33: 0,
      FKL47: 11500000,
      los: 15,
      peer_group_id: '4_1_3_1',
      secondary_diagnoses: [],
    },
    {
      claim_id: 'CLM-DEMO-UNBUNDLING',
      risk_index: 54.8,
      risk_category: 'MEDIUM_RISK',
      badge_color: '#f59e0b',
      primary_driver: 'Deviasi Biaya (Peer Cost)',
      recommended_action:
        'Verifikasi Terarah: Cek Bukti Top-Up Special CMG & Kesesuaian Paket Tindakan',
      rule_risk_score: 25.0,
      ml_anomaly_score: 72.4,
      rule_violations: ['RULE_SPECIAL_CMG_UNBUNDLING'],
      radar: {
        los_deviation: 24.0,
        cost_deviation: 89.0,
        comorbidity_intensity: 20.0,
        severity_level: 60.0,
        regulatory_violation: 75.0,
      },
      clinical_narrative: [
        'Biaya tagih mencapai 2.63x median kelompok faskes sebaya pada CMG yang sama.',
        'Terpicu aturan Consistency Guardrail: SPECIAL CMG UNBUNDLING.',
      ],
      explanation_text:
        'Indikasi unbundling Special CMG dan kelebihan tagih di atas tarif dasar INA-CBG.',
      cost_peer_ratio: 2.63,
      los_peer_zscore: -0.11,
      comorbidity_count: 1,
      has_severe_comorbidity: 0,
      FKL07: 4,
      FKL08: 1,
      FKL09: 2,
      FKL10: 2,
      FKL14: 1,
      FKL15A: 'I25',
      FKL17A: 'I25',
      FKL18: 'I25.1',
      FKL19: 'I-4-12-II',
      FKL20: 9,
      FKL21: 2,
      FKL23: 2,
      severity_level: 2,
      FKL31: 1,
      FKL32: 6000000,
      FKL33: 4500000,
      FKL47: 15800000,
      los: 3,
      peer_group_id: '4_1_2_1',
      secondary_diagnoses: ['I10'],
    },
    {
      claim_id: 'CLM-DEMO-NORMAL',
      risk_index: 6.4,
      risk_category: 'LOW_RISK',
      badge_color: '#10b981',
      primary_driver: 'Profil Klaim Wajar',
      recommended_action: 'Wajar (Fast-Track Approval)',
      rule_risk_score: 0.0,
      ml_anomaly_score: 14.2,
      rule_violations: [],
      radar: {
        los_deviation: 18.0,
        cost_deviation: 28.0,
        comorbidity_intensity: 0.0,
        severity_level: 30.0,
        regulatory_violation: 0.0,
      },
      clinical_narrative: [
        'Profil klaim konsisten dan berada dalam rentang wajar kelompok fasilitas kesehatan sebaya.',
      ],
      explanation_text:
        'Profil klaim konsisten dan berada dalam rentang wajar kelompok fasilitas kesehatan sebaya.',
      cost_peer_ratio: 0.97,
      los_peer_zscore: -0.12,
      comorbidity_count: 0,
      has_severe_comorbidity: 0,
      FKL07: 4,
      FKL08: 1,
      FKL09: 3,
      FKL10: 2,
      FKL14: 1,
      FKL15A: 'I10',
      FKL17A: 'I10',
      FKL18: 'I10.0',
      FKL19: 'I-4-17-I',
      FKL20: 9,
      FKL21: 4,
      FKL23: 1,
      severity_level: 1,
      FKL31: 1,
      FKL32: 3200000,
      FKL33: 0,
      FKL47: 3100000,
      los: 3,
      peer_group_id: '4_1_3_1',
      secondary_diagnoses: [],
    },
  ];
}
