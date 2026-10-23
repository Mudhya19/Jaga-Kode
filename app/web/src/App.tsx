import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  Award,
  BarChart3,
  Building2,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ClipboardCheck,
  Clock,
  Cpu,
  Database,
  FileCheck2,
  FileSearch,
  FileText,
  Filter,
  FlaskConical,
  History,
  Info,
  Layers,
  Lock,
  Moon,
  Play,
  RefreshCw,
  Search,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sliders,
  Sparkles,
  Sun,
  TrendingUp,
  UserCheck,
  Wallet,
  XCircle,
  Zap,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { FALLBACK_PRESET_CASES, jagaKodeApi } from './services/api';
import type {
  AuditRecordItem,
  BatchEvaluationSummary,
  ClaimEvaluationResponse,
  HealthStatusResponse,
  PeerGroupStatsResponse,
  PresetCaseKey,
  RiskCategory,
  SingleClaimInput,
  VerifierDecision,
} from './types/jagaKode';

type ThemeMode = 'light' | 'dark';

interface PresetScenarioMeta {
  key: PresetCaseKey;
  title: string;
  subtitle: string;
  badge: string;
  expectedTier: RiskCategory;
  description: string;
}

const PRESET_SCENARIOS: PresetScenarioMeta[] = [
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

const HUMAN_DECISIONS = new Set<string>([
  'APPROVED',
  'PENDING_CLARIFICATION',
  'PENDING_VERIFICATION',
  'REJECTED_UPCODING',
]);

function formatDecisionLabel(decision: string | undefined | null): string {
  if (!decision) return '-';
  return decision.replace(/_/g, ' ');
}

function formatRuleLabel(rule: string | undefined | null): string {
  if (!rule) return '';
  return rule.replace(/^RULE_/, '').replace(/_/g, ' ');
}

function formatRiskLabel(category: string | undefined | null): string {
  if (!category) return '-';
  return category.replace(/_/g, ' ');
}

function formatNarrativeText(text: string | undefined | null): string {
  if (!text) return '';
  return text
    .replace(/RULE_([A-Za-z0-9_]+)/g, (_, r) => r.replace(/_/g, ' '))
    .replace(/\bHIGH_RISK\b/g, 'High Risk')
    .replace(/\bMEDIUM_RISK\b/g, 'Medium Risk')
    .replace(/\bLOW_RISK\b/g, 'Low Risk')
    .replace(/\bPENDING_CLARIFICATION\b/g, 'Pending Clarification')
    .replace(/\bREJECTED_UPCODING\b/g, 'Rejected Upcoding')
    .replace(/\bPROFIL_KLAIM_WAJAR\b/g, 'Profil Klaim Wajar');
}

function syncInaCbgWithSeverity(fkl19: string, sev: number): string {
  const roman = sev === 3 ? 'III' : sev === 2 ? 'II' : 'I';
  const trimmed = fkl19.trim().toUpperCase();
  if (!trimmed) return `I-4-17-${roman}`;
  if (/-(III|II|I|0|1|2|3)$/.test(trimmed)) {
    return trimmed.replace(/-(III|II|I|0|1|2|3)$/, `-${roman}`);
  }
  return trimmed;
}

function inferSeverityFromInaCbg(fkl19: string, fallbackSev: number): number {
  const trimmed = fkl19.trim().toUpperCase();
  if (trimmed.endsWith('-III') || trimmed.endsWith('-3')) return 3;
  if (trimmed.endsWith('-II') || trimmed.endsWith('-2')) return 2;
  if (trimmed.endsWith('-I') || trimmed.endsWith('-1')) return 1;
  return fallbackSev;
}

const PERMENKES_RULES_CATALOG = [
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

const QUICK_NOTE_TEMPLATES: Record<string, string[]> = {
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

function formatRupiah(amount: number | undefined | null, compact = false): string {
  const safeVal = typeof amount === 'number' && Number.isFinite(amount) ? amount : 0;
  if (compact) {
    if (Math.abs(safeVal) >= 1_000_000_000) {
      return `Rp ${(safeVal / 1_000_000_000).toLocaleString('id-ID', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })} M`;
    }
    if (Math.abs(safeVal) >= 1_000_000) {
      return `Rp ${(safeVal / 1_000_000).toLocaleString('id-ID', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      })} Jt`;
    }
  }
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(safeVal);
}

function estimateClaimDisputeIdr(claim: ClaimEvaluationResponse): number {
  if (claim.risk_category === 'LOW_RISK') return 0;
  const billed = claim.FKL47 ?? 0;
  const standard = claim.FKL32 && claim.FKL32 > 0 ? claim.FKL32 : billed;
  const directDiff = Math.max(0, billed - standard);
  const ratio = claim.cost_peer_ratio ?? 1;
  const peerDiff = ratio > 1.05 && billed > 0 ? Math.max(0, billed - billed / ratio) : 0;
  return Math.round(Math.max(directDiff, peerDiff));
}

function buildFallbackEvaluatedClaims(): ClaimEvaluationResponse[] {
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

export default function App() {
  // 1. Opsi C Dual-Theme State (Default: Clean Clinical Light Mode)
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem('jaga_kode_theme');
    return saved === 'dark' ? 'dark' : 'light';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('jaga_kode_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  // 2. Backend Connection & Telemetry State
  const [apiKeyInput, setApiKeyInput] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [showApiConfig, setShowApiConfig] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthStatusResponse | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean>(true);
  const [loadingInitial, setLoadingInitial] = useState<boolean>(true);
  const [statusBanner, setStatusBanner] = useState<{
    type: 'success' | 'warning' | 'error' | 'info';
    text: string;
  } | null>(null);

  // 3. Smart Triage Queue & Filters State
  const [claimsQueue, setClaimsQueue] = useState<ClaimEvaluationResponse[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<'ALL' | RiskCategory>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [auditedClaimsMap, setAuditedClaimsMap] = useState<Record<string, VerifierDecision>>({});

  // 4. Preset Cases, Custom Claim Evaluator & Batch Summary State
  const [presetMap, setPresetMap] =
    useState<Record<PresetCaseKey, SingleClaimInput>>(FALLBACK_PRESET_CASES);
  const [activePresetKey, setActivePresetKey] = useState<PresetCaseKey | null>(null);
  const [showCustomForm, setShowCustomForm] = useState<boolean>(false);
  const [evaluatingClaim, setEvaluatingClaim] = useState<boolean>(false);
  const [runningBatch, setRunningBatch] = useState<boolean>(false);
  const [batchSummary, setBatchSummary] = useState<BatchEvaluationSummary | null>(null);

  const [formInput, setFormInput] = useState<SingleClaimInput>(
    FALLBACK_PRESET_CASES.ghost_comorbidity
  );
  const [secondaryDiagText, setSecondaryDiagText] = useState<string>('N17.9, I50.9, A41.9');

  // 5. Peer Group Stats State
  const [peerStats, setPeerStats] = useState<PeerGroupStatsResponse | null>(null);
  const [loadingPeerStats, setLoadingPeerStats] = useState<boolean>(false);

  // 6. Human-in-the-Loop Audit State
  const [selectedDecision, setSelectedDecision] =
    useState<VerifierDecision>('REJECTED_UPCODING');
  const [verifierId, setVerifierId] = useState<string>('VERIF-BPJS-01');
  const [verifierNotes, setVerifierNotes] = useState<string>('');
  const [disputePreventedInput, setDisputePreventedInput] = useState<number>(0);
  const [submittingAudit, setSubmittingAudit] = useState<boolean>(false);
  const [auditHistory, setAuditHistory] = useState<AuditRecordItem[]>([]);
  const [auditValidationError, setAuditValidationError] = useState<string | null>(null);

  // Selected claim object
  const selectedClaim = useMemo<ClaimEvaluationResponse | null>(() => {
    if (!claimsQueue.length) return null;
    return (
      claimsQueue.find((c) => c.claim_id === selectedClaimId) || claimsQueue[0] || null
    );
  }, [claimsQueue, selectedClaimId]);

  // Clear unsent clinical notes when switching between different claims
  useEffect(() => {
    setVerifierNotes('');
    setAuditValidationError(null);
  }, [selectedClaim?.claim_id]);

  // Synchronize form & audit defaults when selectedClaim changes
  useEffect(() => {
    if (!selectedClaim) return;
    const estSavings = estimateClaimDisputeIdr(selectedClaim);
    setDisputePreventedInput(estSavings);

    if (selectedClaim.risk_category === 'HIGH_RISK') {
      setSelectedDecision('REJECTED_UPCODING');
    } else if (selectedClaim.risk_category === 'MEDIUM_RISK') {
      setSelectedDecision('PENDING_CLARIFICATION');
    } else {
      setSelectedDecision('APPROVED');
    }
    setAuditValidationError(null);

    // Fetch Peer Group stats for the selected claim
    const pgId =
      selectedClaim.peer_group_id ||
      `${selectedClaim.FKL07 ?? 4}_${selectedClaim.FKL08 ?? 1}_${selectedClaim.FKL09 ?? 3}_${selectedClaim.FKL31 ?? 1}`;
    const cmgVal = selectedClaim.FKL20 ?? 9;

    let cancelled = false;
    setLoadingPeerStats(true);
    jagaKodeApi
      .getPeerGroupStats(pgId, cmgVal, apiKey)
      .then((res) => {
        if (!cancelled) setPeerStats(res);
      })
      .catch(() => {
        if (!cancelled) {
          setPeerStats({
            peer_group_id: pgId,
            cmg: cmgVal,
            resolution_level: 'level_2_peer_group',
            profile: {
              count: 142,
              mean_los: 3.1,
              std_los: 1.8,
              median_cost: selectedClaim.FKL32 || 3680400,
              iqr_cost: 1450000,
              mean_comorbidity: 0.85,
              std_comorbidity: 1.1,
              severity_3_ratio: 0.048,
            },
            total_peer_cmg_profiles: 4036,
            total_peer_groups: 316,
            global_profile: {
              count: 195544,
              mean_los: 3.41,
              std_los: 3.7,
              median_cost: 3680400,
              iqr_cost: 3079800,
              mean_comorbidity: 0.97,
              std_comorbidity: 1.26,
              severity_3_ratio: 0.049,
            },
          });
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingPeerStats(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedClaim, apiKey]);

  // Initial Data Load from FastAPI
  const loadWorkspaceData = useCallback(async () => {
    setLoadingInitial(true);
    try {
      const [healthRes, sampleRes, presetsRes, recentAuditsRes] = await Promise.all([
        jagaKodeApi.getHealth(apiKey),
        jagaKodeApi.getSampleClaims(50, 'ALL', apiKey),
        jagaKodeApi.getPresetCases(apiKey).catch(() => FALLBACK_PRESET_CASES),
        jagaKodeApi.getRecentAudits(20, apiKey).catch(() => []),
      ]);

      setHealth(healthRes);
      setApiOnline(true);
      setPresetMap(presetsRes);
      setAuditHistory(recentAuditsRes);

      const initialAudited: Record<string, VerifierDecision> = {};
      for (const item of recentAuditsRes) {
        const cid = item.claim_id_raw;
        const dec = item.verifier_decision;
        if (cid && dec && HUMAN_DECISIONS.has(dec)) {
          initialAudited[cid] = dec as VerifierDecision;
        }
      }
      setAuditedClaimsMap(initialAudited);

      if (sampleRes && sampleRes.length > 0) {
        setClaimsQueue(sampleRes);
        setSelectedClaimId((prev) => prev || sampleRes[0].claim_id);
      } else {
        const fb = buildFallbackEvaluatedClaims();
        setClaimsQueue(fb);
        setSelectedClaimId(fb[0].claim_id);
      }
    } catch (err) {
      setApiOnline(false);
      const fb = buildFallbackEvaluatedClaims();
      setClaimsQueue(fb);
      setSelectedClaimId(fb[0].claim_id);
      setStatusBanner({
        type: 'warning',
        text: `Mode Simulasi Lokal Aktif — Backend FastAPI belum terhubung (${
          err instanceof Error ? err.message : 'Offline'
        }).`,
      });
    } finally {
      setLoadingInitial(false);
    }
  }, [apiKey]);

  useEffect(() => {
    loadWorkspaceData();
  }, [loadWorkspaceData]);

  // Filtered queue based on risk category & search query
  const filteredQueue = useMemo(() => {
    return claimsQueue.filter((item) => {
      if (categoryFilter !== 'ALL' && item.risk_category !== categoryFilter) {
        return false;
      }
      if (!searchQuery.trim()) return true;
      const q = searchQuery.trim().toLowerCase();
      const matchId = item.claim_id.toLowerCase().includes(q);
      const matchCbg = (item.FKL19 || '').toLowerCase().includes(q);
      const matchDiag = (item.FKL17A || '').toLowerCase().includes(q);
      const matchDriver = (item.primary_driver || '').toLowerCase().includes(q);
      const matchRules = item.rule_violations.some((r) => r.toLowerCase().includes(q));
      return matchId || matchCbg || matchDiag || matchDriver || matchRules;
    });
  }, [claimsQueue, categoryFilter, searchQuery]);

  // Executive KPI Aggregations
  const kpiStats = useMemo(() => {
    const total = claimsQueue.length;
    const highCount = claimsQueue.filter((c) => c.risk_category === 'HIGH_RISK').length;
    const medCount = claimsQueue.filter((c) => c.risk_category === 'MEDIUM_RISK').length;
    const lowCount = claimsQueue.filter((c) => c.risk_category === 'LOW_RISK').length;
    const fastTrackPct = total > 0 ? Math.round((lowCount / total) * 1000) / 10 : 0;

    const totalBilled = claimsQueue.reduce((acc, c) => acc + (c.FKL47 ?? 0), 0);
    const highRiskBilled = claimsQueue
      .filter((c) => c.risk_category === 'HIGH_RISK')
      .reduce((acc, c) => acc + (c.FKL47 ?? 0), 0);

    const potentialDisputeIdr = claimsQueue.reduce(
      (acc, c) => acc + estimateClaimDisputeIdr(c),
      0
    );

    // Deduplicate by claim_id_raw so only the latest human decision per claim is counted
    const latestSavingsByClaim = new Map<string, number>();
    for (let i = 0; i < auditHistory.length; i += 1) {
      const a = auditHistory[i];
      if (!a.verifier_decision || !HUMAN_DECISIONS.has(a.verifier_decision)) {
        continue;
      }
      const key = a.claim_id_raw || a.claim_pseudo_id || `idx-${i}`;
      const val =
        a.verifier_decision === 'APPROVED'
          ? 0
          : typeof a.dispute_prevented_idr === 'number' && Number.isFinite(a.dispute_prevented_idr)
          ? Math.max(0, a.dispute_prevented_idr)
          : 0;
      latestSavingsByClaim.set(key, val);
    }
    let confirmedAuditSavingsIdr = 0;
    for (const val of latestSavingsByClaim.values()) {
      confirmedAuditSavingsIdr += val;
    }

    return {
      total,
      highCount,
      medCount,
      lowCount,
      fastTrackPct,
      totalBilled,
      highRiskBilled,
      potentialDisputeIdr,
      confirmedAuditSavingsIdr,
    };
  }, [claimsQueue, auditHistory]);

  // Populate simulator form from currently selected claim
  const handleLoadClaimToSimulator = (claim: ClaimEvaluationResponse) => {
    const rawSev = claim.severity_level ?? claim.FKL23 ?? 1;
    const normSev = Math.min(3, Math.max(1, rawSev));
    const cbgCode = syncInaCbgWithSeverity(claim.FKL19 || 'I-4-17-I', normSev);
    const inputObj: SingleClaimInput = {
      FKL02: claim.claim_id,
      FKL07: claim.FKL07 ?? 4,
      FKL08: claim.FKL08 ?? 1,
      FKL09: claim.FKL09 ?? 3,
      FKL10: claim.FKL10 ?? 2,
      FKL14: claim.FKL14 ?? 1,
      FKL15A: claim.FKL15A || claim.FKL17A || 'I10',
      FKL17A: claim.FKL17A || 'I10',
      FKL18: claim.FKL18 || claim.FKL17A || 'I10.0',
      FKL19: cbgCode,
      FKL20: claim.FKL20 ?? 9,
      FKL21: claim.FKL21 ?? 4,
      FKL23: normSev,
      FKL31: claim.FKL31 ?? 1,
      FKL32: claim.FKL32 && claim.FKL32 > 0 ? claim.FKL32 : claim.FKL47 ?? 3200000,
      FKL33: claim.FKL33 ?? 0,
      FKL47: claim.FKL47 ?? 3100000,
      los: claim.los ?? 3,
      secondary_diagnoses: claim.secondary_diagnoses || [],
      peer_group_id: claim.peer_group_id || '4_1_3_1',
    };
    setFormInput(inputObj);
    setSecondaryDiagText((claim.secondary_diagnoses || []).join(', '));
    setShowCustomForm(true);
  };

  // 1-Click Live Demo Preset Evaluation
  const handleTriggerPresetScenario = async (presetKey: PresetCaseKey) => {
    setActivePresetKey(presetKey);
    setEvaluatingClaim(true);
    setStatusBanner(null);

    try {
      let presetClaim: SingleClaimInput;
      try {
        presetClaim = await jagaKodeApi.getSinglePresetCase(presetKey, apiKey);
      } catch {
        presetClaim = presetMap[presetKey] || FALLBACK_PRESET_CASES[presetKey];
      }

      setFormInput(presetClaim);
      setSecondaryDiagText((presetClaim.secondary_diagnoses || []).join(', '));

      const evalRes = await jagaKodeApi.evaluateSingleClaim(presetClaim, apiKey);
      const enriched: ClaimEvaluationResponse = {
        ...evalRes,
        FKL07: presetClaim.FKL07,
        FKL08: presetClaim.FKL08,
        FKL09: presetClaim.FKL09,
        FKL10: presetClaim.FKL10,
        FKL14: presetClaim.FKL14,
        FKL15A: presetClaim.FKL15A || presetClaim.FKL17A,
        FKL17A: presetClaim.FKL17A,
        FKL18: presetClaim.FKL18 || presetClaim.FKL17A,
        FKL19: presetClaim.FKL19,
        FKL20: presetClaim.FKL20,
        FKL21: presetClaim.FKL21,
        FKL23: presetClaim.FKL23,
        FKL31: presetClaim.FKL31,
        FKL32: presetClaim.FKL32 && presetClaim.FKL32 > 0 ? presetClaim.FKL32 : presetClaim.FKL47,
        FKL33: presetClaim.FKL33 ?? 0,
        FKL47: presetClaim.FKL47,
        los: presetClaim.los,
        peer_group_id:
          presetClaim.peer_group_id ||
          `${presetClaim.FKL07}_${presetClaim.FKL08}_${presetClaim.FKL09}_${presetClaim.FKL31}`,
        secondary_diagnoses: presetClaim.secondary_diagnoses || [],
      };

      setClaimsQueue((prev) => {
        const without = prev.filter((c) => c.claim_id !== enriched.claim_id);
        return [enriched, ...without];
      });
      setSelectedClaimId(enriched.claim_id);
      setCategoryFilter('ALL');
      setApiOnline(true);
      setStatusBanner({
        type: 'info',
        text: `Skenario Demo "${presetKey.replace(/_/g, ' ').toUpperCase()}" dievaluasi real-time: Skor Risiko ${enriched.risk_index}/100 [${formatRiskLabel(enriched.risk_category)}].`,
      });
    } catch (err) {
      const fbList = buildFallbackEvaluatedClaims();
      const match =
        fbList.find((c) =>
          c.claim_id.toLowerCase().includes(presetKey.split('_')[0].toLowerCase())
        ) || fbList[0];
      setClaimsQueue((prev) => [match, ...prev.filter((c) => c.claim_id !== match.claim_id)]);
      setSelectedClaimId(match.claim_id);
      setStatusBanner({
        type: 'warning',
        text: `Evaluasi Preset menggunakan fallback lokal: ${
          err instanceof Error ? err.message : 'Error'
        }`,
      });
    } finally {
      setEvaluatingClaim(false);
    }
  };

  // Custom Claim Form Evaluation (POST /api/v1/claims/evaluate)
  const handleEvaluateCustomClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    setEvaluatingClaim(true);
    setStatusBanner(null);

    const parsedSec = secondaryDiagText
      .split(/[,;\s]+/)
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean);

    const syncedFkl19 = syncInaCbgWithSeverity(
      formInput.FKL19.trim().toUpperCase() || 'I-4-17-I',
      formInput.FKL23
    );

    const payload: SingleClaimInput = {
      ...formInput,
      FKL02: formInput.FKL02.trim() || 'CLM-CUSTOM-2026',
      FKL17A: formInput.FKL17A.trim().toUpperCase() || 'I10',
      FKL19: syncedFkl19,
      secondary_diagnoses: parsedSec,
    };

    try {
      const evalRes = await jagaKodeApi.evaluateSingleClaim(payload, apiKey);
      const enriched: ClaimEvaluationResponse = {
        ...evalRes,
        FKL07: payload.FKL07,
        FKL08: payload.FKL08,
        FKL09: payload.FKL09,
        FKL10: payload.FKL10,
        FKL14: payload.FKL14,
        FKL15A: payload.FKL15A || payload.FKL17A,
        FKL17A: payload.FKL17A,
        FKL18: payload.FKL18 || payload.FKL17A,
        FKL19: payload.FKL19,
        FKL20: payload.FKL20,
        FKL21: payload.FKL21,
        FKL23: payload.FKL23,
        FKL31: payload.FKL31,
        FKL32: payload.FKL32 && payload.FKL32 > 0 ? payload.FKL32 : payload.FKL47,
        FKL33: payload.FKL33 ?? 0,
        FKL47: payload.FKL47,
        los: payload.los,
        peer_group_id:
          payload.peer_group_id ||
          `${payload.FKL07}_${payload.FKL08}_${payload.FKL09}_${payload.FKL31}`,
        secondary_diagnoses: parsedSec,
      };

      setClaimsQueue((prev) => [
        enriched,
        ...prev.filter((c) => c.claim_id !== enriched.claim_id),
      ]);
      setSelectedClaimId(enriched.claim_id);
      setCategoryFilter('ALL');
      setStatusBanner({
        type: 'success',
        text: `Klaim "${enriched.claim_id}" berhasil dievaluasi • Skor Risiko: ${enriched.risk_index}/100 (${formatRiskLabel(enriched.risk_category)}).`,
      });
    } catch (err) {
      setStatusBanner({
        type: 'error',
        text: `Gagal mengevaluasi klaim kustom: ${
          err instanceof Error ? err.message : 'Kesalahan input'
        }`,
      });
    } finally {
      setEvaluatingClaim(false);
    }
  };

  // Batch Evaluation (POST /api/v1/claims/batch-evaluate)
  const handleRunBatchSimulation = async () => {
    setRunningBatch(true);
    setStatusBanner(null);
    try {
      const claimsToBatch = Object.values(presetMap);
      const summary = await jagaKodeApi.evaluateBatchClaims(claimsToBatch, apiKey);
      setBatchSummary(summary);

      // Merge evaluated preset claims into top of queue with their input metadata
      const enrichedResults = summary.results.map((r, idx) => {
        const src = claimsToBatch[idx];
        return {
          ...r,
          FKL07: src.FKL07,
          FKL08: src.FKL08,
          FKL09: src.FKL09,
          FKL10: src.FKL10,
          FKL14: src.FKL14,
          FKL15A: src.FKL15A || src.FKL17A,
          FKL17A: src.FKL17A,
          FKL18: src.FKL18 || src.FKL17A,
          FKL19: src.FKL19,
          FKL20: src.FKL20,
          FKL21: src.FKL21,
          FKL23: src.FKL23,
          FKL31: src.FKL31,
          FKL32: src.FKL32 && src.FKL32 > 0 ? src.FKL32 : src.FKL47,
          FKL33: src.FKL33 ?? 0,
          FKL47: src.FKL47,
          los: src.los,
          peer_group_id:
            src.peer_group_id || `${src.FKL07}_${src.FKL08}_${src.FKL09}_${src.FKL31}`,
          secondary_diagnoses: src.secondary_diagnoses || [],
        };
      });

      setClaimsQueue((prev) => {
        const batchIds = new Set(enrichedResults.map((e) => e.claim_id));
        const rest = prev.filter((p) => !batchIds.has(p.claim_id));
        return [...enrichedResults, ...rest].sort((a, b) => b.risk_index - a.risk_index);
      });
      if (enrichedResults.length > 0) {
        setSelectedClaimId(enrichedResults[0].claim_id);
      }
      setStatusBanner({
        type: 'success',
        text: `Evaluasi Batch (${summary.total_claims} klaim) selesai: ${summary.high_risk_count} High Risk, ${summary.medium_risk_count} Medium Risk, Fast-Track ${summary.fast_track_percentage}%, Potensi Penghematan ${formatRupiah(
          summary.total_disputed_potential_idr
        )}.`,
      });
    } catch (err) {
      setStatusBanner({
        type: 'error',
        text: `Gagal menjalankan batch evaluasi: ${
          err instanceof Error ? err.message : 'Error'
        }`,
      });
    } finally {
      setRunningBatch(false);
    }
  };

  // Submit Verifier Audit Decision (POST /api/v1/audit/action)
  const handleSubmitAuditDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClaim) return;

    const trimmedNotes = verifierNotes.trim();
    if (trimmedNotes.length < 5) {
      setAuditValidationError(
        'Catatan klinis verifikator wajib diisi (minimal 5 karakter) sesuai SOP Kepatuhan Audit BPJS Kesehatan.'
      );
      return;
    }
    if (/[<>]|\$\{/.test(trimmedNotes)) {
      setAuditValidationError(
        'Catatan tidak boleh mengandung karakter tag HTML (<, >) atau ekspresi injeksi.'
      );
      return;
    }

    setAuditValidationError(null);
    setSubmittingAudit(true);

    const effectiveDispute =
      selectedDecision === 'APPROVED' ? 0 : Math.max(0, Number(disputePreventedInput) || 0);

    try {
      const res = await jagaKodeApi.recordAuditAction(
        {
          claim_id: selectedClaim.claim_id,
          decision: selectedDecision,
          verifier_id: verifierId.trim() || 'VERIF-BPJS-01',
          verifier_notes: trimmedNotes,
          dispute_prevented_idr: effectiveDispute,
          risk_index: selectedClaim.risk_index,
          risk_category: selectedClaim.risk_category,
          primary_driver: selectedClaim.primary_driver,
        },
        apiKey
      );

      setAuditedClaimsMap((prev) => ({
        ...prev,
        [selectedClaim.claim_id]: selectedDecision,
      }));
      setVerifierNotes('');

      const updatedHistory = await jagaKodeApi.getRecentAudits(20, apiKey);
      setAuditHistory(updatedHistory);
      setStatusBanner({
        type: 'success',
        text: `${res.message} (ID Pseudonim UU PDP: ${res.audit_id})`,
      });
    } catch (err) {
      setAuditValidationError(
        err instanceof Error ? err.message : 'Gagal menyimpan keputusan audit.'
      );
    } finally {
      setSubmittingAudit(false);
    }
  };

  // Radar Chart 5-Axis Data
  const radarChartData = useMemo(() => {
    if (!selectedClaim) return [];
    const r = selectedClaim.radar;
    return [
      {
        axis: 'Consistency Rule',
        labelId: 'Pelanggaran Regulasi Permenkes',
        score: r.regulatory_violation,
        baseline: 15,
      },
      {
        axis: 'Peer Cost Dev.',
        labelId: 'Deviasi Biaya Peer Group',
        score: r.cost_deviation,
        baseline: 30,
      },
      {
        axis: 'LoS Anomaly',
        labelId: 'Anomali Lama Rawat (LoS)',
        score: r.los_deviation,
        baseline: 25,
      },
      {
        axis: 'Severity Jump',
        labelId: 'Lonjakan Severity INA-CBG',
        score: r.severity_level,
        baseline: 33,
      },
      {
        axis: 'Diagnosis Rarity',
        labelId: 'Kompleksitas & Komorbiditas',
        score: r.comorbidity_intensity,
        baseline: 20,
      },
    ];
  }, [selectedClaim]);

  // Financial Comparison BarChart Data (FKL47 vs FKL32 vs Peer Median)
  const costComparisonData = useMemo(() => {
    if (!selectedClaim) return [];
    const billed = selectedClaim.FKL47 ?? 0;
    const standardCbg =
      selectedClaim.FKL32 && selectedClaim.FKL32 > 0 ? selectedClaim.FKL32 : billed;
    const peerMedian =
      peerStats?.profile?.median_cost ??
      (selectedClaim.cost_peer_ratio > 0
        ? Math.round(billed / selectedClaim.cost_peer_ratio)
        : standardCbg);

    return [
      {
        name: 'Tarif INA-CBG (FKL32)',
        nominal: Math.round(standardCbg),
        color: '#00529C',
      },
      {
        name: 'Median Peer Group',
        nominal: Math.round(peerMedian),
        color: '#10b981',
      },
      {
        name: 'Tagihan RS (FKL47)',
        nominal: Math.round(billed),
        color:
          selectedClaim.risk_category === 'HIGH_RISK'
            ? '#ef4444'
            : selectedClaim.risk_category === 'MEDIUM_RISK'
            ? '#f59e0b'
            : '#10b981',
      },
    ];
  }, [selectedClaim, peerStats]);

  const isDark = theme === 'dark';

  const renderRiskBadge = (category: RiskCategory) => {
    if (category === 'HIGH_RISK') {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/15 px-2.5 py-1 text-xs font-bold text-red-600 dark:bg-red-500/20 dark:text-red-400 border border-red-500/30">
          <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
          HIGH RISK
        </span>
      );
    }
    if (category === 'MEDIUM_RISK') {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/15 px-2.5 py-1 text-xs font-bold text-amber-700 dark:bg-amber-500/20 dark:text-amber-300 border border-amber-500/30">
          <span className="h-2 w-2 rounded-full bg-amber-500" />
          MEDIUM RISK
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-bold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 border border-emerald-500/30">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        FAST-TRACK
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#0b1120] dark:text-slate-100 transition-colors duration-200">
      {/* ================= TOP COMMAND HEADER (OPSI C DUAL THEME) ================= */}
      <header className="sticky top-0 z-30 border-b border-slate-200/90 bg-white/95 backdrop-blur-md dark:border-slate-800 dark:bg-[#0f172a]/95 shadow-xs">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          {/* Brand Identity */}
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[#00529C] to-emerald-600 text-white shadow-md shadow-emerald-600/20">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-lg font-extrabold tracking-tight text-[#00529C] dark:text-white sm:text-xl">
                  JAGA-KODE
                </h1>
                <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 text-[11px] font-bold tracking-wide text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 border border-emerald-500/30">
                  AI GUARDRAIL FKRTL
                </span>
                <span className="hidden rounded-md bg-[#00529C]/10 px-2 py-0.5 text-[11px] font-semibold text-[#00529C] dark:bg-sky-500/15 dark:text-sky-300 md:inline-block">
                  Healthkathon BPJS Kesehatan 2026 • Tim SI DANDANG
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Smart Triage & Explainable AI untuk Deteksi Upcoding Diagnosis & Tindakan INA-CBG
                (BEA Domain C03.04)
              </p>
            </div>
          </div>

          {/* Right Controls: Telemetry, API Key, Refresh, Opsi C Dual-Theme Switch */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* FastAPI Microservice Health Pill */}
            <div
              className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium ${
                apiOnline
                  ? 'border-emerald-500/30 bg-emerald-50/80 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-950/40 dark:text-emerald-300'
                  : 'border-amber-500/40 bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
              }`}
              title={
                health
                  ? `${health.project} (${health.version}) — ${health.environment}`
                  : 'Status Koneksi API'
              }
            >
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  apiOnline ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                }`}
              />
              <span className="font-bold">
                API {apiOnline ? health?.status || 'ONLINE' : 'SIMULASI'}
              </span>
              <span className="hidden text-slate-400 sm:inline">|</span>
              <span className="hidden sm:inline">
                {(health?.peer_profiles_count ?? 4036).toLocaleString('id-ID')} Profil Faskes
              </span>
            </div>

            {/* Optional API Key Config Button */}
            <button
              type="button"
              onClick={() => setShowApiConfig((v) => !v)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-100/80 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 cursor-pointer"
              title="Konfigurasi X-API-Key (Opsional)"
            >
              <Lock className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              <span className="hidden md:inline">Auth</span>
            </button>

            {/* Reload Queue Button */}
            <button
              type="button"
              onClick={loadWorkspaceData}
              disabled={loadingInitial}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 cursor-pointer disabled:opacity-50"
              title="Muat Ulang Antrean Klaim & Jejak Audit"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loadingInitial ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Sinkronisasi</span>
            </button>

            {/* OPSI C: Dual Theme Toggle Button (Clean Clinical Light <-> Command-Center Dark) */}
            <button
              type="button"
              onClick={toggleTheme}
              aria-label="Sakelar Tema Visual Opsi C"
              className="inline-flex items-center gap-2 rounded-lg border border-[#00529C]/25 bg-gradient-to-r from-[#00529C] to-emerald-600 px-3 py-1.5 text-xs font-bold text-white shadow-xs hover:opacity-95 dark:border-emerald-500/40 dark:from-emerald-600 dark:to-sky-700 cursor-pointer"
            >
              {isDark ? (
                <>
                  <Sun className="h-3.5 w-3.5 text-amber-300" />
                  <span>Clinical Light Mode</span>
                </>
              ) : (
                <>
                  <Moon className="h-3.5 w-3.5 text-emerald-100" />
                  <span>Command Dark Mode</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Optional API Key Bar */}
        {showApiConfig && (
          <div className="border-t border-slate-200 bg-slate-50 px-4 py-2 dark:border-slate-800 dark:bg-slate-900/90">
            <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                <Lock className="h-3.5 w-3.5 text-emerald-600" />
                <span>
                  Header Keamanan <code className="font-mono font-bold">X-API-Key</code> (kosongkan
                  jika variabel lingkungan <code className="font-mono">JAGA_KODE_API_KEY</code> tidak
                  diaktifkan di server):
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Masukkan X-API-Key opsional..."
                  className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                />
                <button
                  type="button"
                  onClick={loadWorkspaceData}
                  className="rounded-md bg-emerald-600 px-3 py-1 font-semibold text-white hover:bg-emerald-700 cursor-pointer"
                >
                  Terapkan
                </button>
              </div>
            </div>
          </div>
        )}
      </header>

      {/*MAIN CONTAINER*/}
      <main className="mx-auto max-w-[1600px] space-y-5 px-4 py-5 sm:px-6">
        {/* Notification Banner */}
        {statusBanner && (
          <div
            className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-2.5 text-xs font-medium shadow-2xs ${
              statusBanner.type === 'success'
                ? 'border-emerald-500/40 bg-emerald-50 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-200'
                : statusBanner.type === 'error'
                ? 'border-red-500/40 bg-red-50 text-red-900 dark:bg-red-950/50 dark:text-red-200'
                : statusBanner.type === 'warning'
                ? 'border-amber-500/40 bg-amber-50 text-amber-900 dark:bg-amber-950/50 dark:text-amber-200'
                : 'border-sky-500/40 bg-sky-50 text-sky-900 dark:bg-sky-950/50 dark:text-sky-200'
            }`}
          >
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 shrink-0" />
              <span>{statusBanner.text}</span>
            </div>
            <button
              type="button"
              onClick={() => setStatusBanner(null)}
              className="text-xs font-bold underline opacity-75 hover:opacity-100 cursor-pointer"
            >
              Tutup
            </button>
          </div>
        )}

        {/* ================= FEATURE 1: EXECUTIVE KPI & FINANCIAL IMPACT SIMULATOR BANNER ================= */}
        <section
          aria-label="Executive KPI & Financial Impact Simulator"
          className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-[#111827] sm:p-5"
        >
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00529C]/10 text-[#00529C] dark:bg-sky-500/20 dark:text-sky-400">
                <TrendingUp className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white sm:text-base">
                  Executive KPI & Simulasi Dampak Finansial Dana Jaminan Sosial (DJS)
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Ringkasan triase real-time antrean FKRTL & kalkulasi potensi penghematan pencegahan
                  upcoding
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300">
                <Award className="h-3.5 w-3.5" />
                Precision@100: 100.0% • PR-AUC: 0.9339 • Lift@5%: 8.05x
              </span>
              <button
                type="button"
                onClick={handleRunBatchSimulation}
                disabled={runningBatch}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#00529C] px-3 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-[#003f7a] dark:bg-emerald-600 dark:hover:bg-emerald-500 cursor-pointer disabled:opacity-50"
              >
                <Zap className="h-3.5 w-3.5" />
                <span>
                  {runningBatch
                    ? 'Memproses Batch...'
                    : 'Evaluasi Otomatis 5 Skenario'}
                </span>
              </button>
            </div>
          </div>

          {/* 4 Executive KPI Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Card 1: Total Klaim & Nilai Tagihan */}
            <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Total Antrean Klaim Aktif
                </span>
                <Database className="h-4 w-4 text-[#00529C] dark:text-sky-400" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-slate-900 dark:text-white">
                  {kpiStats.total}
                </span>
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  berkas RITL (Sampel dari 195.544)
                </span>
              </div>
              <div className="mt-2 flex items-center justify-between border-t border-slate-200/70 pt-2 text-xs dark:border-slate-800">
                <span className="text-slate-500 dark:text-slate-400">Total Tagihan (FKL47):</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  {formatRupiah(kpiStats.totalBilled, true)}
                </span>
              </div>
            </div>

            {/* Card 2: Efisiensi Fast-Track */}
            <div className="rounded-xl border border-emerald-500/25 bg-emerald-50/40 p-4 dark:border-emerald-500/20 dark:bg-emerald-950/20">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                  Jalur Cepat (Fast-Track)
                </span>
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-emerald-700 dark:text-emerald-400">
                  {kpiStats.fastTrackPct}%
                </span>
                <span className="text-xs font-medium text-emerald-700/80 dark:text-emerald-300/80">
                  ({kpiStats.lowCount} Klaim Low Risk)
                </span>
              </div>
              <div className="mt-2 flex items-center justify-between border-t border-emerald-500/20 pt-2 text-xs">
                <span className="text-emerald-800/80 dark:text-emerald-300/80">
                  Populasi Empiris RITL:
                </span>
                <span className="font-bold text-emerald-800 dark:text-emerald-300">
                  94.34% Lolos Otomatis
                </span>
              </div>
            </div>

            {/* Card 3: Klaim Prioritas Audit Tinggi & Sedang */}
            <div className="rounded-xl border border-red-500/25 bg-red-50/40 p-4 dark:border-red-500/20 dark:bg-red-950/20">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-red-800 dark:text-red-300">
                  Prioritas Audit (High & Med)
                </span>
                <ShieldAlert className="h-4 w-4 text-red-600 dark:text-red-400" />
              </div>
              <div className="mt-2 flex items-baseline gap-3">
                <span className="text-2xl font-extrabold text-red-600 dark:text-red-400">
                  {kpiStats.highCount} Merah
                </span>
                <span className="text-sm font-bold text-amber-600 dark:text-amber-400">
                  • {kpiStats.medCount} Kuning
                </span>
              </div>
              <div className="mt-2 flex items-center justify-between border-t border-red-500/20 pt-2 text-xs">
                <span className="text-red-800/80 dark:text-red-300/80">
                  Eksposur Tagihan High-Risk:
                </span>
                <span className="font-bold text-red-700 dark:text-red-300">
                  {formatRupiah(kpiStats.highRiskBilled, true)}
                </span>
              </div>
            </div>

            {/* Card 4: Estimasi Penghematan Dana JKN / Pencegahan Dispute */}
            <div className="rounded-xl border border-[#00529C]/25 bg-gradient-to-br from-[#00529C]/5 to-emerald-500/10 p-4 dark:border-sky-500/30 dark:from-sky-950/40 dark:to-emerald-950/30">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-[#00529C] dark:text-sky-300">
                  Estimasi Penyelamatan Dana JKN
                </span>
                <Wallet className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-xl font-extrabold text-[#00529C] dark:text-emerald-400 sm:text-2xl">
                  {formatRupiah(kpiStats.potentialDisputeIdr, true)}
                </span>
              </div>
              <div className="mt-2 flex items-center justify-between border-t border-[#00529C]/15 pt-2 text-xs dark:border-sky-500/20">
                <span className="text-slate-600 dark:text-slate-300">
                  Terkonfirmasi Audit Verifikator:
                </span>
                <span className="font-bold text-emerald-700 dark:text-emerald-300">
                  {formatRupiah(kpiStats.confirmedAuditSavingsIdr, true)}
                </span>
              </div>
            </div>
          </div>

          {/* Batch Evaluation Summary Result Ribbon (shown after clicking Batch Evaluate) */}
          {batchSummary && (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-xs dark:border-emerald-500/30 dark:bg-emerald-950/40">
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-bold text-emerald-800 dark:text-emerald-300">
                  Hasil Evaluasi Otomatis Batch Klaim:
                </span>
                <span>
                  Total: <strong>{batchSummary.total_claims} klaim</strong>
                </span>
                <span>•</span>
                <span className="text-red-600 dark:text-red-400 font-semibold">
                  High Risk: {batchSummary.high_risk_count}
                </span>
                <span>•</span>
                <span className="text-amber-600 dark:text-amber-400 font-semibold">
                  Medium Risk: {batchSummary.medium_risk_count}
                </span>
                <span>•</span>
                <span className="text-emerald-700 dark:text-emerald-300 font-semibold">
                  Low Risk: {batchSummary.low_risk_count} ({batchSummary.fast_track_percentage}%
                  Fast-Track)
                </span>
                <span>•</span>
                <span>
                  Tagihan Batch: <strong>{formatRupiah(batchSummary.total_billed_idr)}</strong>
                </span>
                <span>•</span>
                <span>
                  Potensi Penghematan Dispute:{' '}
                  <strong className="text-emerald-700 dark:text-emerald-300">
                    {formatRupiah(batchSummary.total_disputed_potential_idr)}
                  </strong>
                </span>
              </div>
              <button
                type="button"
                onClick={() => setBatchSummary(null)}
                className="text-xs font-semibold underline opacity-75 hover:opacity-100 cursor-pointer"
              >
                Sembunyikan
              </button>
            </div>
          )}
        </section>

        {/* ================= 1-CLICK LIVE DEMO SIMULATOR & CUSTOM EVALUATOR ================= */}
        <section
          aria-label="1-Click Live Demo Simulator & Custom Claim Evaluator"
          className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-[#111827] sm:p-5"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400">
                <FlaskConical className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white sm:text-base">
                  1-Click Live Demo Simulator (5 Skenario Uji Juri Healthkathon) & Custom Claim
                  Evaluator
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Pilih salah satu skenario klinis di bawah ini untuk menguji deteksi anomali AI
                  Guardrail secara instan.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowCustomForm((prev) => !prev)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 cursor-pointer"
            >
              <Sliders className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>
                {showCustomForm
                  ? 'Tutup Form Simulator Klaim Kustom'
                  : 'Buka Form Simulator Klaim Kustom'}
              </span>
              {showCustomForm ? (
                <ChevronUp className="h-3.5 w-3.5" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" />
              )}
            </button>
          </div>

          {/* 5 Preset Buttons Grid */}
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {PRESET_SCENARIOS.map((scn) => {
              const isSelected = activePresetKey === scn.key;
              const isNormal = scn.expectedTier === 'LOW_RISK';
              return (
                <button
                  key={scn.key}
                  type="button"
                  disabled={evaluatingClaim}
                  onClick={() => handleTriggerPresetScenario(scn.key)}
                  className={`group flex flex-col justify-between rounded-xl border p-3.5 text-left transition-all cursor-pointer ${
                    isSelected
                      ? 'border-emerald-500 bg-emerald-50/70 ring-2 ring-emerald-500/30 dark:border-emerald-400 dark:bg-emerald-950/40'
                      : 'border-slate-200 bg-slate-50/60 hover:border-emerald-500/50 hover:bg-white dark:border-slate-800 dark:bg-slate-900/60 dark:hover:border-emerald-500/50 dark:hover:bg-slate-900'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-extrabold uppercase ${
                          isNormal
                            ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                            : 'bg-red-500/15 text-red-600 dark:text-red-400'
                        }`}
                      >
                        {formatRiskLabel(scn.badge)}
                      </span>
                      <Play className="h-3.5 w-3.5 text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400" />
                    </div>
                    <h3 className="mt-2 text-xs font-bold text-slate-900 dark:text-white">
                      {scn.title}
                    </h3>
                    <p className="mt-0.5 font-mono text-[11px] font-semibold text-[#00529C] dark:text-sky-400">
                      {scn.subtitle}
                    </p>
                    <p className="mt-1.5 text-[11px] leading-relaxed text-slate-500 dark:text-slate-400">
                      {scn.description}
                    </p>
                  </div>
                  <div className="mt-3 flex items-center justify-between border-t border-slate-200/70 pt-2 text-[11px] font-semibold text-emerald-700 dark:border-slate-800 dark:text-emerald-400">
                    <span>Uji Skenario 1-Klik</span>
                    <span>→</span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Interactive Custom Claim Evaluator Form */}
          {showCustomForm && (
            <form
              onSubmit={handleEvaluateCustomClaim}
              className="mt-4 rounded-xl border border-slate-200 bg-slate-50/90 p-4 dark:border-slate-800 dark:bg-slate-900/80"
            >
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#00529C] dark:text-sky-400">
                  Parameter Input Klaim FKRTL (Kontrak Skema SingleClaimInput)
                </h3>
                <span className="text-[11px] text-slate-500 dark:text-slate-400">
                  Ubah variabel klinis/biaya di bawah ini untuk menguji respons mesin Dual-Guardrail
                  secara langsung
                </span>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Claim ID (FKL02)
                  </label>
                  <input
                    type="text"
                    required
                    value={formInput.FKL02}
                    onChange={(e) => setFormInput({ ...formInput, FKL02: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Diagnosis Primer (FKL17A)
                  </label>
                  <input
                    type="text"
                    required
                    value={formInput.FKL17A}
                    onChange={(e) =>
                      setFormInput({
                        ...formInput,
                        FKL17A: e.target.value.toUpperCase(),
                        FKL15A: e.target.value.toUpperCase(),
                      })
                    }
                    placeholder="Misal: I10, E11, J18"
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Kode INA-CBG (FKL19)
                  </label>
                  <input
                    type="text"
                    required
                    value={formInput.FKL19}
                    onChange={(e) =>
                      setFormInput({ ...formInput, FKL19: e.target.value.toUpperCase() })
                    }
                    placeholder="Misal: I-4-17-III"
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Severity Level (FKL23)
                  </label>
                  <select
                    value={formInput.FKL23}
                    onChange={(e) =>
                      setFormInput({ ...formInput, FKL23: Number(e.target.value) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-800"
                  >
                    <option value={1}>Level I (Ringan)</option>
                    <option value={2}>Level II (Sedang)</option>
                    <option value={3}>Level III (Berat / MCC)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Lama Rawat / LoS (Hari)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={365}
                    required
                    value={formInput.los}
                    onChange={(e) =>
                      setFormInput({ ...formInput, los: Math.max(0, Number(e.target.value)) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Status Pulang (FKL14)
                  </label>
                  <select
                    value={formInput.FKL14}
                    onChange={(e) =>
                      setFormInput({ ...formInput, FKL14: Number(e.target.value) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-800"
                  >
                    <option value={1}>1 - Sembuh / Atas Persetujuan Dokter</option>
                    <option value={2}>2 - Dirujuk ke RS Lain</option>
                    <option value={3}>3 - Meninggal Dunia</option>
                    <option value={4}>4 - Pulang Paksa (APS)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Tarif Acuan INA-CBG (FKL32 Rp)
                  </label>
                  <input
                    type="number"
                    min={0}
                    step={50000}
                    value={formInput.FKL32 ?? 0}
                    onChange={(e) =>
                      setFormInput({ ...formInput, FKL32: Math.max(0, Number(e.target.value)) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Tagihan RS (FKL47 Rp)
                  </label>
                  <input
                    type="number"
                    min={0}
                    step={50000}
                    required
                    value={formInput.FKL47}
                    onChange={(e) =>
                      setFormInput({ ...formInput, FKL47: Math.max(0, Number(e.target.value)) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs font-bold text-red-600 dark:border-slate-700 dark:bg-slate-800 dark:text-red-400"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Top-Up Special CMG (FKL33 Rp)
                  </label>
                  <input
                    type="number"
                    min={0}
                    step={50000}
                    value={formInput.FKL33 ?? 0}
                    onChange={(e) =>
                      setFormInput({ ...formInput, FKL33: Math.max(0, Number(e.target.value)) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Kode CMG (FKL20) & Peer Group
                  </label>
                  <div className="mt-1 flex gap-1.5">
                    <input
                      type="number"
                      min={1}
                      max={30}
                      value={formInput.FKL20}
                      onChange={(e) =>
                        setFormInput({ ...formInput, FKL20: Number(e.target.value) })
                      }
                      className="w-16 rounded-lg border border-slate-300 bg-white px-2 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                      title="Kode CMG (FKL20)"
                    />
                    <input
                      type="text"
                      value={formInput.peer_group_id || '4_1_3_1'}
                      onChange={(e) =>
                        setFormInput({ ...formInput, peer_group_id: e.target.value })
                      }
                      placeholder="4_1_3_1"
                      className="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                      title="Peer Group ID (Kepemilikan_Jenis_Kelas_Regional)"
                    />
                  </div>
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                    Diagnosis Sekunder ICD-10 (Pisahkan dengan koma)
                  </label>
                  <div className="mt-1 flex gap-2">
                    <input
                      type="text"
                      value={secondaryDiagText}
                      onChange={(e) => setSecondaryDiagText(e.target.value)}
                      placeholder="Contoh: N17.9, I50.9, A41.9"
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                    />
                    <button
                      type="submit"
                      disabled={evaluatingClaim}
                      className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-emerald-700 cursor-pointer disabled:opacity-50"
                    >
                      <Cpu className="h-3.5 w-3.5" />
                      <span>{evaluatingClaim ? 'Mengevaluasi...' : 'Evaluasi Klaim'}</span>
                    </button>
                  </div>
                </div>
              </div>
            </form>
          )}
        </section>

        {/* ================= MAIN WORKSPACE SPLIT: LEFT TRIAGE QUEUE (5 COLS) + RIGHT INSPECTOR & AUDIT (7 COLS) ================= */}
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
          {/* LEFT COLUMN: SMART TRIAGE QUEUE PANEL */}
          <div className="lg:col-span-5 flex flex-col rounded-2xl border border-slate-200/90 bg-white shadow-xs dark:border-slate-800 dark:bg-[#111827]">
            <div className="border-b border-slate-200 p-4 dark:border-slate-800">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-[#00529C] dark:text-sky-400" />
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                    Smart Triage Queue (Antrean Berbasis Prioritas Risiko)
                  </h2>
                </div>
                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  {filteredQueue.length} / {claimsQueue.length} Klaim
                </span>
              </div>

              {/* Filter Tabs */}
              <div className="mt-3 flex flex-wrap gap-1.5">
                {(
                  [
                    { id: 'ALL', label: `Semua (${kpiStats.total})` },
                    { id: 'HIGH_RISK', label: `High Risk (${kpiStats.highCount})` },
                    { id: 'MEDIUM_RISK', label: `Medium (${kpiStats.medCount})` },
                    { id: 'LOW_RISK', label: `Fast-Track (${kpiStats.lowCount})` },
                  ] as const
                ).map((tab) => {
                  const active = categoryFilter === tab.id;
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setCategoryFilter(tab.id)}
                      className={`rounded-lg px-2.5 py-1 text-xs font-bold transition-colors cursor-pointer ${
                        active
                          ? 'bg-[#00529C] text-white dark:bg-emerald-600'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
                      }`}
                    >
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Search Input */}
              <div className="relative mt-3">
                <Search className="pointer-events-none absolute top-1/2 left-3 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Cari ID Klaim (FKL02), Kode INA-CBG (FKL19), ICD-10, atau Aturan..."
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pr-3 pl-8 text-xs text-slate-800 placeholder:text-slate-400 focus:border-emerald-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                />
              </div>
            </div>

            {/* Scrollable Claims Queue Cards */}
            <div className="max-h-[820px] overflow-y-auto p-2.5 space-y-2.5">
              {filteredQueue.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 dark:text-slate-400">
                  Tidak ada klaim yang cocok dengan filter atau kata kunci pencarian.
                </div>
              ) : (
                filteredQueue.map((item, idx) => {
                  const isSelected = selectedClaim?.claim_id === item.claim_id;
                  const auditStatus = auditedClaimsMap[item.claim_id];
                  return (
                    <div
                      key={item.claim_id}
                      onClick={() => setSelectedClaimId(item.claim_id)}
                      className={`group flex flex-col gap-2.5 rounded-xl border p-3.5 transition-all cursor-pointer ${
                        isSelected
                          ? 'border-emerald-600 bg-emerald-50/90 shadow-xs ring-1 ring-emerald-500/30 dark:border-emerald-500 dark:bg-emerald-950/40'
                          : 'border-slate-200/80 bg-white hover:border-slate-300 hover:shadow-xs dark:border-slate-800/90 dark:bg-slate-900/50 dark:hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2.5">
                        <div className="flex items-start gap-2.5 min-w-0 flex-1">
                          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-200/80 font-mono text-[10px] font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300 mt-0.5">
                            {idx + 1}
                          </span>
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span className="font-mono text-xs font-extrabold text-slate-900 truncate dark:text-white">
                                {item.claim_id}
                              </span>
                              {auditStatus && (
                                <span className="rounded bg-[#00529C]/15 px-1.5 py-0.5 text-[10px] font-bold text-[#00529C] dark:bg-sky-500/20 dark:text-sky-300">
                                  ✓ {formatDecisionLabel(auditStatus)}
                                </span>
                              )}
                            </div>
                            <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                              <span className="font-mono font-semibold text-[#00529C] dark:text-sky-400">
                                {item.FKL19 || 'INA-CBG'}
                              </span>
                              <span>•</span>
                              <span>ICD-10: {item.FKL17A || 'N/A'}</span>
                              <span>•</span>
                              <span>LoS: {item.los ?? '-'} hr</span>
                              <span>•</span>
                              <span>Peer: {item.cost_peer_ratio}x</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex shrink-0 flex-col items-end gap-1">
                          {renderRiskBadge(item.risk_category)}
                          <span className="font-mono text-xs font-extrabold text-slate-800 dark:text-slate-200">
                            CPS: {item.risk_index.toFixed(1)}/100
                          </span>
                        </div>
                      </div>

                      {/* Progress Bar & Financial Row */}
                      <div className="flex items-center justify-between gap-3">
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${Math.min(100, Math.max(4, item.risk_index))}%`,
                              backgroundColor: item.badge_color,
                            }}
                          />
                        </div>
                        <span className="shrink-0 font-mono text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                          {formatRupiah(item.FKL47, true)}
                        </span>
                      </div>

                      {/* Rule Violation Pills */}
                      <div className="flex flex-wrap items-center justify-between gap-1.5 pt-0.5">
                        <div className="flex flex-wrap items-center gap-1 min-w-0 flex-1">
                          {item.rule_violations.length > 0 ? (
                            item.rule_violations.map((rv) => (
                              <span
                                key={rv}
                                className="rounded bg-red-500/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-red-700 dark:bg-red-500/20 dark:text-red-300 border border-red-500/20"
                              >
                                {formatRuleLabel(rv)}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-slate-400 dark:text-slate-500">
                              Driver: {formatDecisionLabel(item.primary_driver)}
                            </span>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedClaimId(item.claim_id);
                            handleLoadClaimToSimulator(item);
                          }}
                          className="shrink-0 text-[11px] font-semibold text-[#00529C] opacity-0 group-hover:opacity-100 hover:underline dark:text-sky-400 cursor-pointer"
                        >
                          Uji di Simulator →
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* RIGHT COLUMN: CLAIM DETAIL INSPECTOR, 5-AXIS XAI RADAR & HUMAN-IN-THE-LOOP AUDIT */}
          <div className="lg:col-span-7 space-y-5">
            {selectedClaim ? (
              <>
                {/* ================= FEATURE 3: CLAIM DETAIL INSPECTOR & 5-AXIS EXPLAINABILITY RADAR (XAI) ================= */}
                <section
                  aria-label="Claim Detail Inspector & 5-Axis Explainability Radar"
                  className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-[#111827] sm:p-5"
                >
                  {/* Inspector Header */}
                  <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-4 dark:border-slate-800">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-[#00529C] dark:text-sky-400">
                          Claim Detail Inspector
                        </span>
                        {renderRiskBadge(selectedClaim.risk_category)}
                        {auditedClaimsMap[selectedClaim.claim_id] && (
                          <span className="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs font-bold text-emerald-700 dark:text-emerald-300">
                            Keputusan Verifikator: {auditedClaimsMap[selectedClaim.claim_id]}
                          </span>
                        )}
                      </div>
                      <h2 className="mt-1 font-mono text-lg font-extrabold text-slate-900 dark:text-white sm:text-xl">
                        {selectedClaim.claim_id}
                      </h2>
                      <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                        INA-CBG:{' '}
                        <strong className="font-mono text-slate-800 dark:text-slate-200">
                          {selectedClaim.FKL19 || 'N/A'}
                        </strong>{' '}
                        • Diagnosis Primer:{' '}
                        <strong className="font-mono text-slate-800 dark:text-slate-200">
                          {selectedClaim.FKL17A || 'N/A'}
                        </strong>{' '}
                        ({selectedClaim.FKL18 || selectedClaim.FKL17A}) • Peer Group:{' '}
                        <strong className="font-mono text-slate-800 dark:text-slate-200">
                          {selectedClaim.peer_group_id || '4_1_3_1'}
                        </strong>{' '}
                        (CMG {selectedClaim.FKL20 ?? '-'})
                      </p>
                    </div>

                    {/* Dual-Guardrail Score Pills */}
                    <div className="flex items-center gap-2.5">
                      <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-center dark:border-slate-800 dark:bg-slate-900">
                        <div className="text-[10px] font-semibold uppercase text-slate-500 dark:text-slate-400">
                          Rule Score (55%)
                        </div>
                        <div className="font-mono text-sm font-extrabold text-slate-800 dark:text-slate-100">
                          {selectedClaim.rule_risk_score.toFixed(1)}
                        </div>
                      </div>
                      <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-center dark:border-slate-800 dark:bg-slate-900">
                        <div className="text-[10px] font-semibold uppercase text-slate-500 dark:text-slate-400">
                          ML Anomaly (45%)
                        </div>
                        <div className="font-mono text-sm font-extrabold text-slate-800 dark:text-slate-100">
                          {selectedClaim.ml_anomaly_score.toFixed(1)}
                        </div>
                      </div>
                      <div
                        className="rounded-xl px-3.5 py-2 text-center text-white shadow-xs"
                        style={{ backgroundColor: selectedClaim.badge_color }}
                      >
                        <div className="text-[10px] font-bold uppercase opacity-90">
                          Composite CPS
                        </div>
                        <div className="font-mono text-base font-extrabold">
                          {selectedClaim.risk_index.toFixed(1)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Recommended Action Banner */}
                  <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-[#00529C]/20 bg-[#00529C]/5 p-3 text-xs dark:border-sky-500/30 dark:bg-sky-950/30">
                    <FileSearch className="mt-0.5 h-4 w-4 shrink-0 text-[#00529C] dark:text-sky-400" />
                    <div>
                      <span className="font-bold text-[#00529C] dark:text-sky-300">
                        Rekomendasi Tindak Lanjut SOP Verifikator:{' '}
                      </span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {selectedClaim.recommended_action}
                      </span>
                      <div className="mt-1 text-[11px] text-slate-600 dark:text-slate-400">
                        Faktor Pemicu Dominan:{' '}
                        <code className="font-mono font-bold">{formatRuleLabel(selectedClaim.primary_driver)}</code>
                      </div>
                    </div>
                  </div>

                  {/* 2-Column Visual XAI Grid: 5-Axis Radar Chart + Financial & Peer Comparison */}
                  <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                    {/* 5-Axis Explainability Radar Chart */}
                    <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3.5 dark:border-slate-800 dark:bg-slate-900/50">
                      <div className="mb-2 flex items-center justify-between">
                        <div>
                          <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                            5-Axis Explainability Radar (XAI)
                          </h3>
                          <p className="text-[11px] text-slate-500 dark:text-slate-400">
                            Profil Risiko Klaim vs Ambang Normal Peer Group
                          </p>
                        </div>
                        <Activity className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                      </div>

                      <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart
                            cx="50%"
                            cy="50%"
                            outerRadius="72%"
                            data={radarChartData}
                          >
                            <PolarGrid
                              stroke={isDark ? '#334155' : '#cbd5e1'}
                              strokeDasharray="3 3"
                            />
                            <PolarAngleAxis
                              dataKey="axis"
                              tick={{
                                fill: isDark ? '#e2e8f0' : '#1e293b',
                                fontSize: 11,
                                fontWeight: 600,
                              }}
                            />
                            <PolarRadiusAxis
                              angle={90}
                              domain={[0, 100]}
                              tick={{ fill: isDark ? '#94a3b8' : '#64748b', fontSize: 10 }}
                            />
                            <Radar
                              name="Ambang Normal Peer"
                              dataKey="baseline"
                              stroke="#10b981"
                              fill="#10b981"
                              fillOpacity={0.18}
                            />
                            <Radar
                              name="Skor Klaim Ini"
                              dataKey="score"
                              stroke={selectedClaim.badge_color}
                              fill={selectedClaim.badge_color}
                              fillOpacity={0.45}
                            />
                            <Legend wrapperStyle={{ fontSize: '11px' }} />
                            <Tooltip
                              content={({ active, payload }) => {
                                if (active && payload && payload.length) {
                                  const p = payload[0];
                                  return (
                                    <div className="rounded-xl border border-slate-200 bg-white/95 p-2.5 shadow-lg backdrop-blur-xs dark:border-slate-700 dark:bg-slate-900/95">
                                      <p className="text-xs font-bold text-[#00529C] dark:text-sky-400">
                                        {p.name || (p.payload as any)?.metric || 'Metrik XAI'}
                                      </p>
                                      <p className="mt-1 font-mono text-xs font-extrabold text-slate-800 dark:text-slate-100">
                                        Skor: {p.value} / 100
                                      </p>
                                    </div>
                                  );
                                }
                                return null;
                              }}
                            />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Financial & Peer Group Comparison (FKL47 vs FKL32 vs Peer Median) */}
                    <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3.5 dark:border-slate-800 dark:bg-slate-900/50">
                      <div className="mb-2 flex items-center justify-between">
                        <div>
                          <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                            Perbandingan Tagihan RS (FKL47) vs Standar INA-CBG (FKL32)
                          </h3>
                          <p className="text-[11px] text-slate-500 dark:text-slate-400">
                            Referensi Peer Group:{' '}
                            <span className="font-mono font-semibold">
                              {peerStats?.peer_group_id || selectedClaim.peer_group_id || 'Global'}
                            </span>{' '}
                            ({peerStats?.resolution_level ? peerStats.resolution_level.replace(/_/g, ' ') : 'Kelompok Sebaya'})
                          </p>
                        </div>
                        <BarChart3 className="h-4 w-4 text-[#00529C] dark:text-sky-400" />
                      </div>

                      <div className="h-44 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={costComparisonData}
                            layout="vertical"
                            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                              stroke={isDark ? '#1e293b' : '#e2e8f0'}
                            />
                            <XAxis
                              type="number"
                              tickFormatter={(v) => `${(Number(v) / 1_000_000).toFixed(1)}Jt`}
                              tick={{ fill: isDark ? '#94a3b8' : '#475569', fontSize: 10 }}
                            />
                            <YAxis
                              type="category"
                              dataKey="name"
                              width={125}
                              tick={{
                                fill: isDark ? '#e2e8f0' : '#1e293b',
                                fontSize: 10,
                                fontWeight: 600,
                              }}
                            />
                            <Tooltip
                              content={({ active, payload, label }) => {
                                if (active && payload && payload.length) {
                                  const val = payload[0].value as number;
                                  return (
                                    <div className="rounded-xl border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur-xs dark:border-slate-700 dark:bg-slate-900/95">
                                      <p className="text-xs font-bold text-[#00529C] dark:text-sky-400">
                                        {label}
                                      </p>
                                      <p className="mt-1 font-mono text-xs font-semibold text-slate-800 dark:text-slate-200">
                                        Nominal:{' '}
                                        <span className="font-extrabold text-emerald-600 dark:text-emerald-400">
                                          {formatRupiah(val)}
                                        </span>
                                      </p>
                                    </div>
                                  );
                                }
                                return null;
                              }}
                            />
                            <Bar dataKey="nominal" radius={[0, 6, 6, 0]}>
                              {costComparisonData.map((entry, i) => (
                                <Cell key={i} fill={entry.color} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      {/* Peer Group Statistical Telemetry Cards */}
                      <div className="mt-2 grid grid-cols-3 gap-2 border-t border-slate-200/80 pt-2.5 text-center dark:border-slate-800">
                        <div className="rounded-lg bg-white p-2 dark:bg-slate-800/90">
                          <div className="text-[10px] text-slate-500 dark:text-slate-400">
                            Rasio Biaya Peer
                          </div>
                          <div className="font-mono text-xs font-extrabold text-slate-900 dark:text-white">
                            {selectedClaim.cost_peer_ratio.toFixed(2)}x
                          </div>
                        </div>
                        <div className="rounded-lg bg-white p-2 dark:bg-slate-800/90">
                          <div className="text-[10px] text-slate-500 dark:text-slate-400">
                            LoS Klaim vs Peer
                          </div>
                          <div className="font-mono text-xs font-extrabold text-slate-900 dark:text-white">
                            {selectedClaim.los ?? 0} hr vs{' '}
                            {(peerStats?.profile?.mean_los ?? 3.4).toFixed(1)} hr
                          </div>
                        </div>
                        <div className="rounded-lg bg-white p-2 dark:bg-slate-800/90">
                          <div className="text-[10px] text-slate-500 dark:text-slate-400">
                            Z-Score LoS Peer
                          </div>
                          <div className="font-mono text-xs font-extrabold text-slate-900 dark:text-white">
                            {selectedClaim.los_peer_zscore >= 0 ? '+' : ''}
                            {selectedClaim.los_peer_zscore.toFixed(2)} SD
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Secondary Diagnoses & Clinical Narrative Box */}
                  <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-3 dark:border-slate-800 dark:bg-slate-900/50">
                      <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
                        Bukti Narasi Klinis XAI (Clinical Narrative):
                      </div>
                      <ul className="mt-1.5 space-y-1 text-xs text-slate-600 dark:text-slate-300">
                        {selectedClaim.clinical_narrative.map((line, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="font-bold text-emerald-600 dark:text-emerald-400">
                              •
                            </span>
                            <span>{formatNarrativeText(line)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-3 dark:border-slate-800 dark:bg-slate-900/50">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          Diagnosis Sekunder (FKL24) & Atribut Klinis:
                        </span>
                        <span className="rounded bg-slate-200 px-1.5 py-0.5 font-mono text-[10px] font-bold dark:bg-slate-800">
                          {selectedClaim.comorbidity_count} Komorbiditas
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {selectedClaim.secondary_diagnoses &&
                        selectedClaim.secondary_diagnoses.length > 0 ? (
                          selectedClaim.secondary_diagnoses.map((code) => (
                            <span
                              key={code}
                              className="rounded-md border border-slate-300 bg-white px-2 py-0.5 font-mono text-xs font-bold text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                            >
                              ICD-10: {code}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs italic text-slate-400">
                            Tidak ada diagnosis sekunder yang diklaimkan
                          </span>
                        )}
                      </div>
                      <div className="mt-2.5 flex flex-wrap gap-3 text-[11px] text-slate-500 dark:text-slate-400">
                        <span>
                          Komorbiditas Mayor (MCC):{' '}
                          <strong className="text-slate-800 dark:text-slate-200">
                            {selectedClaim.has_severe_comorbidity ? 'YA (Terdeteksi)' : 'TIDAK'}
                          </strong>
                        </span>
                        <span>•</span>
                        <span>
                          Estimasi Selisih Dispute:{' '}
                          <strong className="text-red-600 dark:text-red-400">
                            {formatRupiah(estimateClaimDisputeIdr(selectedClaim))}
                          </strong>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 5 Kartu Evaluasi Aturan Klinis Permenkes No. 26/2021 */}
                  <div className="mt-4">
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                        Kartu Pemeriksaan 5 Aturan Klinis Deterministik (Permenkes No. 26/2021 & No.
                        16/2019)
                      </h3>
                      <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                        {selectedClaim.rule_violations.length} dari 5 aturan terpicu
                      </span>
                    </div>

                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      {PERMENKES_RULES_CATALOG.map((rule) => {
                        const violated = selectedClaim.rule_violations.includes(rule.code);
                        return (
                          <div
                            key={rule.code}
                            className={`rounded-xl border p-3 transition-colors ${
                              violated
                                ? 'border-red-500/40 bg-red-50/70 dark:border-red-500/40 dark:bg-red-950/30'
                                : 'border-slate-200/80 bg-white dark:border-slate-800 dark:bg-slate-900/40'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-1.5">
                                {violated ? (
                                  <AlertOctagon className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
                                ) : (
                                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                                )}
                                <span className="font-mono text-xs font-bold text-slate-900 dark:text-white">
                                  {rule.title}
                                </span>
                              </div>
                              <span
                                className={`shrink-0 rounded px-1.5 py-0.5 font-mono text-[10px] font-extrabold ${
                                  violated
                                    ? 'bg-red-600 text-white'
                                    : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                                }`}
                              >
                                {violated ? `TERPICU (+${rule.weight})` : 'PATUH'}
                              </span>
                            </div>
                            <p className="mt-1 text-[11px] font-medium text-[#00529C] dark:text-sky-400">
                              {rule.regulation}
                            </p>
                            <p className="mt-1 text-[11px] leading-relaxed text-slate-600 dark:text-slate-400">
                              {rule.summary}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </section>

                {/* ================= FEATURE 4: HUMAN-IN-THE-LOOP DECISION ACTION & AUDIT TRAIL PANEL ================= */}
                <section
                  aria-label="Human-in-the-Loop Decision Action & Audit Trail"
                  className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-[#111827] sm:p-5"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3 dark:border-slate-800">
                    <div className="flex items-center gap-2">
                      <UserCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                      <div>
                        <h2 className="text-sm font-bold text-slate-900 dark:text-white sm:text-base">
                          Panel Keputusan Verifikator (Human-in-the-Loop) & Jejak Audit UU PDP
                        </h2>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          AI JAGA-KODE bertindak sebagai asisten analitik; keputusan akhir tetap di
                          tangan verifikator BPJS Kesehatan dengan catatan klinis wajib
                        </p>
                      </div>
                    </div>
                    <span className="rounded-md bg-emerald-500/10 px-2.5 py-1 font-mono text-[11px] font-bold text-emerald-700 dark:text-emerald-300">
                      Zero-PII SHA-256 Audit
                    </span>
                  </div>

                  <form onSubmit={handleSubmitAuditDecision} className="mt-4 space-y-4">
                    {/* 3 Decision Action Cards */}
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                      <button
                        type="button"
                        onClick={() => setSelectedDecision('APPROVED')}
                        className={`flex flex-col items-start rounded-xl border p-3 text-left transition-all cursor-pointer ${
                          selectedDecision === 'APPROVED'
                            ? 'border-emerald-600 bg-emerald-50/90 ring-2 ring-emerald-500/30 dark:border-emerald-400 dark:bg-emerald-950/50'
                            : 'border-slate-200 bg-slate-50/60 hover:bg-white dark:border-slate-800 dark:bg-slate-900/50'
                        }`}
                      >
                        <div className="flex w-full items-center justify-between">
                          <span className="rounded bg-emerald-500/20 px-2 py-0.5 font-mono text-[10px] font-extrabold text-emerald-800 dark:text-emerald-300">
                            APPROVED
                          </span>
                          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        </div>
                        <span className="mt-2 text-xs font-bold text-slate-900 dark:text-white">
                          Setujui Klaim (Valid)
                        </span>
                        <span className="mt-1 text-xs text-slate-600 dark:text-slate-300">
                          Bukti rekam medis mendukung penuh kode diagnosis & tindakan.
                        </span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedDecision('PENDING_CLARIFICATION')}
                        className={`flex flex-col items-start rounded-xl border p-3 text-left transition-all cursor-pointer ${
                          selectedDecision === 'PENDING_CLARIFICATION' ||
                          selectedDecision === 'PENDING_VERIFICATION'
                            ? 'border-amber-500 bg-amber-50/90 ring-2 ring-amber-500/30 dark:border-amber-400 dark:bg-amber-950/50'
                            : 'border-slate-200 bg-slate-50/60 hover:bg-white dark:border-slate-800 dark:bg-slate-900/50'
                        }`}
                      >
                        <div className="flex w-full items-center justify-between">
                          <span className="rounded bg-amber-500/20 px-2 py-0.5 font-mono text-[10px] font-extrabold text-amber-800 dark:text-amber-300">
                            PENDING CLARIFICATION
                          </span>
                          <Clock className="h-4 w-4 text-amber-600" />
                        </div>
                        <span className="mt-2 text-xs font-bold text-slate-900 dark:text-white">
                          Tunda / Klarifikasi RM
                        </span>
                        <span className="mt-1 text-xs text-slate-600 dark:text-slate-300">
                          Kembalikan ke Faskes untuk konfirmasi resume medis & bukti penunjang.
                        </span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedDecision('REJECTED_UPCODING')}
                        className={`flex flex-col items-start rounded-xl border p-3 text-left transition-all cursor-pointer ${
                          selectedDecision === 'REJECTED_UPCODING'
                            ? 'border-red-600 bg-red-50/90 ring-2 ring-red-500/30 dark:border-red-400 dark:bg-red-950/50'
                            : 'border-slate-200 bg-slate-50/60 hover:bg-white dark:border-slate-800 dark:bg-slate-900/50'
                        }`}
                      >
                        <div className="flex w-full items-center justify-between">
                          <span className="rounded bg-red-500/20 px-2 py-0.5 font-mono text-[10px] font-extrabold text-red-800 dark:text-red-300">
                            REJECTED UPCODING
                          </span>
                          <XCircle className="h-4 w-4 text-red-600" />
                        </div>
                        <span className="mt-2 text-xs font-bold text-slate-900 dark:text-white">
                          Tolak / Koreksi Kode
                        </span>
                        <span className="mt-1 text-xs text-slate-600 dark:text-slate-300">
                          Koreksi downcode tarif INA-CBG karena bukti komorbiditas/prosedur tidak
                          sah.
                        </span>
                      </button>
                    </div>

                    {/* Verifier ID & Dispute Nominal Row */}
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                          ID Petugas Verifikator BPJS
                        </label>
                        <input
                          type="text"
                          required
                          value={verifierId}
                          onChange={(e) => setVerifierId(e.target.value)}
                          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                          Estimasi Dana DJS Diselamatkan / Koreksi Dispute (Rupiah)
                        </label>
                        <input
                          type="number"
                          min={0}
                          step={50000}
                          value={selectedDecision === 'APPROVED' ? 0 : disputePreventedInput}
                          disabled={selectedDecision === 'APPROVED'}
                          onChange={(e) =>
                            setDisputePreventedInput(Math.max(0, Number(e.target.value)))
                          }
                          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 font-mono text-xs font-bold text-emerald-700 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-emerald-400"
                        />
                      </div>
                    </div>

                    {/* Quick Clinical Note Templates */}
                    <div>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                          Catatan Medis Verifikator (Wajib Diisi — Tersimpan di Audit Trail) *
                        </label>
                        <span className="text-[11px] text-slate-500 dark:text-slate-400">
                          Klik template cepat di bawah atau ketik catatan manual:
                        </span>
                      </div>
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {(QUICK_NOTE_TEMPLATES[selectedDecision] || QUICK_NOTE_TEMPLATES.APPROVED).map(
                          (tpl, i) => (
                            <button
                              key={i}
                              type="button"
                              onClick={() => {
                                setVerifierNotes(tpl);
                                setAuditValidationError(null);
                              }}
                              className="rounded-lg border border-slate-200 bg-slate-100 px-2.5 py-1 text-left text-[11px] font-medium text-slate-700 hover:border-emerald-500 hover:bg-emerald-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 cursor-pointer"
                            >
                              + Gunakan Template SOP #{i + 1}
                            </button>
                          )
                        )}
                      </div>
                      <textarea
                        rows={3}
                        value={verifierNotes}
                        onChange={(e) => {
                          setVerifierNotes(e.target.value);
                          if (auditValidationError) setAuditValidationError(null);
                        }}
                        placeholder="Tuliskan hasil pemeriksaan resume medis, bukti laboratorium, atau alasan koreksi kode INA-CBG..."
                        className="mt-2 w-full rounded-xl border border-slate-300 bg-white p-3 text-xs text-slate-800 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                      />
                      {auditValidationError && (
                        <p className="mt-1 text-xs font-semibold text-red-600 dark:text-red-400">
                          ⚠ {auditValidationError}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center justify-end">
                      <button
                        type="submit"
                        disabled={submittingAudit}
                        className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#00529C] to-emerald-600 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:opacity-95 cursor-pointer disabled:opacity-50"
                      >
                        <Send className="h-3.5 w-3.5" />
                        <span>
                          {submittingAudit
                            ? 'Menyimpan ke Audit Trail...'
                            : `Rekam Keputusan (${formatDecisionLabel(selectedDecision)}) ke Audit Trail`}
                        </span>
                      </button>
                    </div>
                  </form>

                  {/* Live Audit Trail History Table */}
                  <div className="mt-6 border-t border-slate-200 pt-4 dark:border-slate-800">
                    <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <History className="h-4 w-4 text-[#00529C] dark:text-sky-400" />
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                          Log Audit Keputusan Verifikator Real-Time
                        </h3>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-slate-500 dark:text-slate-400">
                          {auditHistory.length} rekaman terbaru
                        </span>
                        {auditHistory.length > 0 && (
                          <button
                            type="button"
                            onClick={() => {
                              if (window.confirm('Bersihkan tampilan riwayat untuk sesi demo ini? (Catatan: Berkas log audit server tetap terlindungi secara permanen)')) {
                                setAuditHistory([]);
                              }
                            }}
                            className="rounded px-2 py-0.5 text-[10px] font-semibold text-slate-500 hover:bg-slate-200 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 cursor-pointer"
                            title="Bersihkan riwayat tampilan layar untuk memulai rekaman sesi demo baru"
                          >
                            Bersihkan Sesi Demo
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="max-h-56 overflow-x-auto overflow-y-auto rounded-xl border border-slate-200 dark:border-slate-800">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-100 text-[11px] font-bold uppercase text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                          <tr>
                            <th className="px-3 py-2">Waktu (UTC)</th>
                            <th className="px-3 py-2">Klaim & Pseudonim SHA-256</th>
                            <th className="px-3 py-2">Keputusan</th>
                            <th className="px-3 py-2">Catatan Medis Verifikator</th>
                            <th className="px-3 py-2 text-right">Dispute Dicegah</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {auditHistory.length === 0 ? (
                            <tr>
                              <td
                                colSpan={5}
                                className="px-3 py-6 text-center text-slate-400 dark:text-slate-500"
                              >
                                Belum ada rekaman jejak audit. Silakan kirim keputusan verifikasi di
                                atas.
                              </td>
                            </tr>
                          ) : (
                            [...auditHistory].reverse().map((rec, idx) => (
                              <tr
                                key={`${rec.claim_pseudo_id || idx}-${rec.timestamp_utc || idx}`}
                                className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40"
                              >
                                <td className="whitespace-nowrap px-3 py-2 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                                  {rec.timestamp_utc
                                    ? new Date(rec.timestamp_utc).toLocaleTimeString('id-ID', {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        second: '2-digit',
                                      })
                                    : '-'}
                                </td>
                                <td className="px-3 py-2">
                                  <div className="font-mono text-xs font-bold text-slate-900 dark:text-white">
                                    {rec.claim_id_raw || '-'}
                                  </div>
                                  <div className="font-mono text-[10px] text-emerald-700 dark:text-emerald-400">
                                    {rec.claim_pseudo_id || ''} • {rec.verifier_id || ''}
                                  </div>
                                </td>
                                <td className="px-3 py-2">
                                  <span
                                    className={`inline-block rounded px-2 py-0.5 font-mono text-[10px] font-bold ${
                                      rec.verifier_decision === 'REJECTED_UPCODING'
                                        ? 'bg-red-500/15 text-red-700 dark:text-red-300'
                                        : rec.verifier_decision === 'APPROVED'
                                        ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                                        : 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
                                    }`}
                                  >
                                    {formatDecisionLabel(rec.verifier_decision)}
                                  </span>
                                </td>
                                <td className="max-w-xs truncate px-3 py-2 text-slate-600 dark:text-slate-300">
                                  {rec.clinical_notes}
                                </td>
                                <td className="whitespace-nowrap px-3 py-2 text-right font-mono font-bold text-emerald-700 dark:text-emerald-400">
                                  {formatRupiah(rec.dispute_prevented_idr)}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </section>
              </>
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900">
                Pilih satu klaim dari antrean di sebelah kiri untuk membuka Claim Detail Inspector.
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-8 border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500 dark:border-slate-800 dark:bg-[#0f172a] dark:text-slate-400">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-2 px-4 sm:px-6">
          <span>
            <strong>JAGA-KODE v2.0</strong> — AI Guardrail untuk Efisiensi Klaim JKN • Tim{' '}
            <strong>SI DANDANG</strong> (Muhammad Dhiauddin, Muhammad Alisyahbana, Muhammad Ali
            Maulana)
          </span>
          <span>
            Kepatuhan: Permenkes No. 26/2021 • Permenkes No. 16/2019 • UU PDP No. 27/2022 (Zero-PII)
          </span>
        </div>
      </footer>
    </div>
  );
}
