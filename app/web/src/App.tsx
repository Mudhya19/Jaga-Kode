import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft, ChevronDown, FlaskConical, Sliders } from 'lucide-react';
import { ApiKeyConfigBar } from './components/layout/ApiKeyConfigBar';
import { Header } from './components/layout/Header';
import { Footer } from './components/common/Footer';
import { NotificationBanner, type BannerInfo } from './components/common/NotificationBanner';
import { ExecutiveKpiBanner, type KpiSummaryStats } from './components/dashboard/ExecutiveKpiBanner';
import { BatchSummaryRibbon } from './components/simulator/BatchSummaryRibbon';
import { CustomClaimForm } from './components/simulator/CustomClaimForm';
import { PresetScenarioGrid } from './components/simulator/PresetScenarioGrid';
import { SmartTriageQueue } from './components/queue/SmartTriageQueue';
import { ClaimDetailInspector } from './components/inspector/ClaimDetailInspector';
import { HumanInTheLoopAudit } from './components/audit/HumanInTheLoopAudit';
import { AuditHistoryTable } from './components/audit/AuditHistoryTable';

import {
  buildFallbackEvaluatedClaims,
  estimateClaimDisputeIdr,
  HUMAN_DECISIONS,
} from './constants/presetScenarios';
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
import {
  formatDecisionLabel,
  formatRiskLabel,
  formatRupiah,
} from './utils/formatters';
import {
  inferSeverityFromInaCbg,
  syncInaCbgWithSeverity,
} from './utils/clinicalHelpers';

type ThemeMode = 'light' | 'dark';

export default function App() {
  // 1. Theme State (Opsi C: Dual Theme — Light Default with Emerald & Blue)
  const [theme, setTheme] = useState<ThemeMode>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('jaga_kode_theme');
      if (saved === 'dark' || saved === 'light') return saved;
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
    }
    return 'light';
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

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  // 2. Telemetry, Auth & Notification State
  const [showApiConfig, setShowApiConfig] = useState<boolean>(false);
  const [apiKey, setApiKey] = useState<string>('');
  const [health, setHealth] = useState<HealthStatusResponse | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean>(false);
  const [loadingInitial, setLoadingInitial] = useState<boolean>(true);
  const [statusBanner, setStatusBanner] = useState<BannerInfo | null>(null);

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

  // 5. Peer Group Statistics State
  const [peerStats, setPeerStats] = useState<PeerGroupStatsResponse | null>(null);
  const [, setLoadingPeerStats] = useState<boolean>(false);

  // 6. Human-in-the-Loop Audit & History State
  const [selectedDecision, setSelectedDecision] =
    useState<VerifierDecision>('REJECTED_UPCODING');
  const [verifierId, setVerifierId] = useState<string>('VERIF-BPJS-0842');
  const [verifierNotes, setVerifierNotes] = useState<string>('');
  const [disputePreventedInput, setDisputePreventedInput] = useState<number>(5300000);
  const [submittingAudit, setSubmittingAudit] = useState<boolean>(false);
  const [auditValidationError, setAuditValidationError] = useState<string | null>(null);
  const [auditHistory, setAuditHistory] = useState<AuditRecordItem[]>([]);

  // Derived: Current Selected Claim
  const selectedClaim = useMemo<ClaimEvaluationResponse | undefined>(() => {
    return claimsQueue.find((c) => c.claim_id === selectedClaimId) || claimsQueue[0];
  }, [claimsQueue, selectedClaimId]);

  // Sync decision when selected claim changes
  useEffect(() => {
    if (!selectedClaim) return;
    if (selectedClaim.risk_category === 'HIGH_RISK') {
      setSelectedDecision('REJECTED_UPCODING');
    } else if (selectedClaim.risk_category === 'MEDIUM_RISK') {
      setSelectedDecision('PENDING_CLARIFICATION');
    } else {
      setSelectedDecision('APPROVED');
    }
    const estimated = estimateClaimDisputeIdr(selectedClaim);
    setDisputePreventedInput(estimated > 0 ? estimated : 3200000);
    setAuditValidationError(null);
  }, [selectedClaim]);

  // Fetch Peer Group Stats
  useEffect(() => {
    if (!selectedClaim) return;
    let cancelled = false;
    setLoadingPeerStats(true);

    jagaKodeApi
      .getPeerGroupStats(selectedClaim.peer_group_id, selectedClaim.FKL20, apiKey)
      .then((res) => {
        if (!cancelled) setPeerStats(res);
      })
      .catch(() => {
        if (!cancelled) {
          setPeerStats({
            peer_group_id: selectedClaim.peer_group_id || '4_1_3_1',
            cmg: selectedClaim.FKL20 ?? 9,
            resolution_level: 'level_2_peer_group',
            total_peer_cmg_profiles: 4036,
            profile: {
              count: 1420,
              mean_los: 3.2,
              std_los: 1.8,
              median_cost: 3680400,
              iqr_cost: 2150000,
              mean_comorbidity: 1.1,
              std_comorbidity: 0.9,
              severity_3_ratio: 0.05,
            },
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

  // Filtered Queue
  const filteredQueue = useMemo(() => {
    let list = claimsQueue;
    if (categoryFilter !== 'ALL') {
      list = list.filter((c) => c.risk_category === categoryFilter);
    }
    const q = searchQuery.trim().toLowerCase();
    if (!q) return list;

    return list.filter((item) => {
      const matchId = item.claim_id.toLowerCase().includes(q);
      const matchCbg = (item.FKL19 || '').toLowerCase().includes(q);
      const matchDiag = (item.FKL17A || '').toLowerCase().includes(q);
      const matchDriver = (item.primary_driver || '').toLowerCase().includes(q);
      const matchRules = item.rule_violations.some((r) => r.toLowerCase().includes(q));
      return matchId || matchCbg || matchDiag || matchDriver || matchRules;
    });
  }, [claimsQueue, categoryFilter, searchQuery]);

  // Executive KPI Summary Stats
  const kpiStats = useMemo<KpiSummaryStats>(() => {
    const total = claimsQueue.length;
    const highCount = claimsQueue.filter((c) => c.risk_category === 'HIGH_RISK').length;
    const medCount = claimsQueue.filter((c) => c.risk_category === 'MEDIUM_RISK').length;
    const lowCount = claimsQueue.filter((c) => c.risk_category === 'LOW_RISK').length;
    const fastTrackPct = total > 0 ? Math.round((lowCount / total) * 100) : 0;
    const totalBilled = claimsQueue.reduce((acc, c) => acc + (c.FKL47 || 0), 0);
    const highRiskBilled = claimsQueue
      .filter((c) => c.risk_category === 'HIGH_RISK')
      .reduce((acc, c) => acc + (c.FKL47 || 0), 0);
    const potentialDisputeIdr = claimsQueue.reduce(
      (acc, c) => acc + estimateClaimDisputeIdr(c),
      0
    );
    const confirmedAuditSavingsIdr = auditHistory.reduce(
      (acc, rec) => acc + (rec.dispute_prevented_idr || 0),
      0
    );

    return {
      total,
      totalBilled,
      lowCount,
      highCount,
      medCount,
      fastTrackPct,
      potentialDisputeIdr,
      highRiskBilled,
      confirmedAuditSavingsIdr,
    };
  }, [claimsQueue, auditHistory]);

  // Load a claim into custom form simulator
  const handleLoadClaimToSimulator = (claim: ClaimEvaluationResponse) => {
    const sev = inferSeverityFromInaCbg(claim.FKL19 || '', claim.severity_level || 1);
    setFormInput({
      FKL02: claim.claim_id,
      FKL07: claim.FKL07 ?? 4,
      FKL08: claim.FKL08 ?? 1,
      FKL09: claim.FKL09 ?? 3,
      FKL10: claim.FKL10 ?? 2,
      FKL14: claim.FKL14 ?? 1,
      FKL15A: claim.FKL15A || claim.FKL17A,
      FKL17A: claim.FKL17A || 'I10',
      FKL18: claim.FKL18 || claim.FKL17A,
      FKL19: claim.FKL19 || 'I-4-17-I',
      FKL20: claim.FKL20 ?? 9,
      FKL21: claim.FKL21 ?? 4,
      FKL23: sev,
      FKL31: claim.FKL31 ?? 1,
      FKL32: claim.FKL32 ?? 3200000,
      FKL33: claim.FKL33 ?? 0,
      FKL47: claim.FKL47 ?? 3200000,
      los: claim.los ?? 3,
      secondary_diagnoses: claim.secondary_diagnoses || [],
      peer_group_id: claim.peer_group_id || '4_1_3_1',
    });
    setSecondaryDiagText((claim.secondary_diagnoses || []).join(', '));
    setShowCustomForm(true);
    setStatusBanner({
      type: 'info',
      text: `Klaim "${claim.claim_id}" berhasil dimuat ke formulir simulator kustom di bawah.`,
    });
  };

  // Trigger 1-Click Preset Scenario
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

      const enrichedRes = await jagaKodeApi.evaluateSingleClaim(presetClaim, apiKey);
      const enriched: ClaimEvaluationResponse = {
        ...enrichedRes,
        FKL07: presetClaim.FKL07,
        FKL08: presetClaim.FKL08,
        FKL09: presetClaim.FKL09,
        FKL10: presetClaim.FKL10,
        FKL14: presetClaim.FKL14,
        FKL15A: presetClaim.FKL15A ?? presetClaim.FKL17A,
        FKL17A: presetClaim.FKL17A,
        FKL18: presetClaim.FKL18 ?? presetClaim.FKL17A,
        FKL19: presetClaim.FKL19,
        FKL20: presetClaim.FKL20,
        FKL21: presetClaim.FKL21,
        FKL23: presetClaim.FKL23,
        severity_level: presetClaim.FKL23,
        FKL31: presetClaim.FKL31,
        FKL32: presetClaim.FKL32 ?? 3200000,
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

  // Evaluate Custom Claim
  const handleEvaluateCustomClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    setEvaluatingClaim(true);
    setStatusBanner(null);

    const parsedSec = secondaryDiagText
      .split(/[,;\s]+/)
      .map((s) => s.trim().toUpperCase())
      .filter((s) => s.length > 0);

    const sev = Number(formInput.FKL23) || 1;
    const syncedCbg = syncInaCbgWithSeverity(formInput.FKL19, sev);

    const payload: SingleClaimInput = {
      ...formInput,
      FKL19: syncedCbg,
      FKL23: sev,
      secondary_diagnoses: parsedSec,
      peer_group_id:
        formInput.peer_group_id ||
        `${formInput.FKL07}_${formInput.FKL08}_${formInput.FKL09}_${formInput.FKL31}`,
    };

    try {
      const enrichedRes = await jagaKodeApi.evaluateSingleClaim(payload, apiKey);
      const enriched: ClaimEvaluationResponse = {
        ...enrichedRes,
        FKL07: payload.FKL07,
        FKL08: payload.FKL08,
        FKL09: payload.FKL09,
        FKL10: payload.FKL10,
        FKL14: payload.FKL14,
        FKL15A: payload.FKL15A ?? payload.FKL17A,
        FKL17A: payload.FKL17A,
        FKL18: payload.FKL18 ?? payload.FKL17A,
        FKL19: payload.FKL19,
        FKL20: payload.FKL20,
        FKL21: payload.FKL21,
        FKL23: payload.FKL23,
        severity_level: payload.FKL23,
        FKL31: payload.FKL31,
        FKL32: payload.FKL32 ?? 3200000,
        FKL33: payload.FKL33 ?? 0,
        FKL47: payload.FKL47,
        los: payload.los,
        peer_group_id: payload.peer_group_id ?? undefined,
        secondary_diagnoses: parsedSec,
      };

      setClaimsQueue((prev) => {
        const without = prev.filter((c) => c.claim_id !== enriched.claim_id);
        return [enriched, ...without];
      });
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

  // Batch Evaluation
  const handleRunBatchSimulation = async () => {
    setRunningBatch(true);
    setStatusBanner(null);
    try {
      const claimsToBatch = Object.values(presetMap);
      const summary = await jagaKodeApi.evaluateBatchClaims(claimsToBatch, apiKey);
      setBatchSummary(summary);

      const enrichedResults: ClaimEvaluationResponse[] = summary.results.map((res, i) => {
        const src = claimsToBatch[i] || {};
        return {
          ...res,
          FKL07: src.FKL07,
          FKL08: src.FKL08,
          FKL09: src.FKL09,
          FKL10: src.FKL10,
          FKL14: src.FKL14,
          FKL15A: src.FKL15A ?? src.FKL17A,
          FKL17A: src.FKL17A,
          FKL18: src.FKL18 ?? src.FKL17A,
          FKL19: src.FKL19,
          FKL20: src.FKL20,
          FKL21: src.FKL21,
          FKL23: src.FKL23,
          severity_level: src.FKL23,
          FKL31: src.FKL31,
          FKL32: src.FKL32 ?? 3200000,
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

  // Full Demo Session Reset
  const handleResetDemoSession = async () => {
    if (
      !window.confirm(
        'Mulai ulang seluruh sesi demo dari awal? Antrean klaim, simulasi, dan tampilan keputusan akan di-refresh ke kondisi default.'
      )
    ) {
      return;
    }
    setLoadingInitial(true);
    try {
      setActivePresetKey(null);
      setBatchSummary(null);
      setCategoryFilter('ALL');
      setSearchQuery('');
      setAuditedClaimsMap({});
      setAuditHistory([]);
      setShowCustomForm(false);
      setFormInput(FALLBACK_PRESET_CASES.ghost_comorbidity);
      setSecondaryDiagText('N17.9, I50.9, A41.9');
      setSelectedDecision('REJECTED_UPCODING');
      setVerifierNotes('');
      setDisputePreventedInput(5300000);

      try {
        await jagaKodeApi.resetDemoAudit(apiKey);
      } catch {
        // Fallback jika API sedang offline
      }

      let sampleRes: ClaimEvaluationResponse[] = [];
      try {
        sampleRes = await jagaKodeApi.getSampleClaims(50, 'ALL', apiKey);
      } catch {
        // Abaikan error
      }

      if (sampleRes && sampleRes.length > 0) {
        setClaimsQueue(sampleRes);
        setSelectedClaimId(sampleRes[0].claim_id);
      } else {
        const fb = buildFallbackEvaluatedClaims();
        setClaimsQueue(fb);
        setSelectedClaimId(fb[0].claim_id);
      }

      setStatusBanner({
        type: 'success',
        text: 'Sesi demo berhasil di-refresh ke kondisi awal. Antrean klaim dan formulir simulasi siap untuk pengujian baru.',
      });
    } catch (err) {
      console.error('Gagal reset sesi demo:', err);
      setStatusBanner({
        type: 'error',
        text: `Gagal me-refresh sesi demo: ${err instanceof Error ? err.message : 'Kesalahan internal'}`,
      });
    } finally {
      setLoadingInitial(false);
    }
  };

  // Submit Verifier Audit Decision
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

    setSubmittingAudit(true);
    setAuditValidationError(null);

    const payload = {
      claim_id: selectedClaim.claim_id,
      decision: selectedDecision,
      verifier_id: verifierId.trim() || 'VERIF-BPJS-0842',
      verifier_notes: trimmedNotes,
      dispute_prevented_idr:
        selectedDecision === 'APPROVED' ? 0 : Number(disputePreventedInput) || 0,
      risk_index: selectedClaim.risk_index,
      risk_category: selectedClaim.risk_category,
      primary_driver: selectedClaim.primary_driver,
    };

    try {
      const res = await jagaKodeApi.recordAuditAction(payload, apiKey);
      setAuditedClaimsMap((prev) => ({
        ...prev,
        [selectedClaim.claim_id]: selectedDecision,
      }));

      const newRecord: AuditRecordItem = {
        timestamp_utc: new Date().toISOString(),
        claim_id_raw: selectedClaim.claim_id,
        claim_pseudo_id: res.audit_id,
        verifier_id: payload.verifier_id,
        risk_index: selectedClaim.risk_index,
        risk_category: selectedClaim.risk_category,
        primary_driver: selectedClaim.primary_driver,
        ai_recommended_action: selectedClaim.recommended_action,
        verifier_decision: selectedDecision,
        clinical_notes: trimmedNotes,
        dispute_prevented_idr: payload.dispute_prevented_idr,
      };

      const updatedHistory = [newRecord, ...auditHistory];
      setAuditHistory(updatedHistory);
      setStatusBanner({
        type: 'success',
        text: `${res.message} (ID Pseudonim UU PDP: ${res.audit_id})`,
      });
    } catch (err) {
      setAuditedClaimsMap((prev) => ({
        ...prev,
        [selectedClaim.claim_id]: selectedDecision,
      }));
      const fallbackAuditId = `CLM-SIM-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
      setAuditHistory((prev) => [
        {
          timestamp_utc: new Date().toISOString(),
          claim_id_raw: selectedClaim.claim_id,
          claim_pseudo_id: fallbackAuditId,
          verifier_id: payload.verifier_id,
          verifier_decision: selectedDecision,
          clinical_notes: trimmedNotes,
          dispute_prevented_idr: payload.dispute_prevented_idr,
        },
        ...prev,
      ]);
      setStatusBanner({
        type: 'info',
        text: `Keputusan "${formatDecisionLabel(selectedDecision)}" dicatat ke sesi lokal (${
          err instanceof Error ? err.message : 'Offline'
        }).`,
      });
    } finally {
      setSubmittingAudit(false);
    }
  };

  const handleClearAuditSession = () => {
    if (
      window.confirm(
        'Bersihkan tampilan riwayat untuk sesi demo ini? (Catatan: Berkas log audit server tetap terlindungi secara permanen)'
      )
    ) {
      setAuditHistory([]);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#0b1120] dark:text-slate-100 transition-colors duration-200">
      {/* Top Command Header */}
      <Header
        health={health}
        apiOnline={apiOnline}
        loadingInitial={loadingInitial}
        showApiConfig={showApiConfig}
        setShowApiConfig={setShowApiConfig}
        loadWorkspaceData={loadWorkspaceData}
        handleResetDemoSession={handleResetDemoSession}
        theme={theme}
        toggleTheme={toggleTheme}
      />

      {/* Optional API Key Bar */}
      <ApiKeyConfigBar
        show={showApiConfig}
        apiKey={apiKey}
        setApiKey={setApiKey}
        onApply={loadWorkspaceData}
      />

      {/* Main Content Workspace */}
      <main className="mx-auto max-w-[1600px] space-y-5 px-4 py-5 sm:px-6">
        {/* Notification Toast Banner */}
        <NotificationBanner
          banner={statusBanner}
          onClose={() => setStatusBanner(null)}
        />

        {/* Feature 1: Executive KPI & Financial Impact Banner */}
        <ExecutiveKpiBanner
          kpiStats={kpiStats}
          runningBatch={runningBatch}
          onRunBatchSimulation={handleRunBatchSimulation}
        />

        {/* Feature 2: 1-Click Live Demo Simulator & Custom Evaluator Section */}
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
                  {showCustomForm
                    ? 'Parameter Input Klaim FKRTL (Custom Claim Evaluator)'
                    : '1-Click Live Demo Simulator (5 Skenario Uji Juri Healthkathon) & Custom Claim Evaluator'}
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {showCustomForm
                    ? 'Ubah variabel klinis dan rincian tarif klaim di bawah ini untuk menguji respons mesin analitik.'
                    : 'Pilih salah satu skenario klinis di bawah ini untuk menguji deteksi anomali AI Guardrail secara instan.'}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowCustomForm((prev) => !prev)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 cursor-pointer"
            >
              {showCustomForm ? (
                <>
                  <ArrowLeft className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>Kembali ke 1-Click Live Demo Simulator</span>
                </>
              ) : (
                <>
                  <Sliders className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>Buka Form Simulator Klaim Kustom</span>
                  <ChevronDown className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>

          {/* 5 Preset Scenario Cards: Sembunyikan saat form parameter kustom dibuka */}
          {!showCustomForm && (
            <PresetScenarioGrid
              activePresetKey={activePresetKey}
              evaluatingClaim={evaluatingClaim}
              onSelectPreset={handleTriggerPresetScenario}
            />
          )}

          {/* Batch Evaluation Summary Ribbon */}
          <BatchSummaryRibbon
            summary={batchSummary}
            onClose={() => setBatchSummary(null)}
          />

          {/* Custom Claim Evaluator Form: Tampil saat dibuka */}
          <CustomClaimForm
            show={showCustomForm}
            formInput={formInput}
            setFormInput={setFormInput}
            secondaryDiagText={secondaryDiagText}
            setSecondaryDiagText={setSecondaryDiagText}
            evaluatingClaim={evaluatingClaim}
            onSubmit={handleEvaluateCustomClaim}
            onBack={() => setShowCustomForm(false)}
          />
        </section>

        {/* Feature 3 & 4: Split Workspace Grid */}
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-12 lg:items-start">
          {/* Left Column: Smart Triage Queue */}
          <SmartTriageQueue
            totalClaimsCount={claimsQueue.length}
            filteredQueue={filteredQueue}
            selectedClaimId={selectedClaimId}
            categoryFilter={categoryFilter}
            setCategoryFilter={setCategoryFilter}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            auditedClaimsMap={auditedClaimsMap}
            onSelectClaim={(id) => setSelectedClaimId(id)}
            onLoadClaimToSimulator={handleLoadClaimToSimulator}
            kpiStats={kpiStats}
          />

          {/* Right Column: Claim Detail Inspector & Human-in-the-Loop Audit */}
          <div className="lg:col-span-7 space-y-5">
            {selectedClaim ? (
              <>
                <ClaimDetailInspector
                  claim={selectedClaim}
                  auditDecision={auditedClaimsMap[selectedClaim.claim_id]}
                  peerStats={peerStats}
                  isDark={theme === 'dark'}
                  apiKey={apiKey}
                  disputeAmount={disputePreventedInput}
                />

                <section
                  aria-label="Human-in-the-Loop Decision Action & Audit Trail"
                  className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-[#111827] sm:p-5"
                >
                  <HumanInTheLoopAudit
                    selectedDecision={selectedDecision}
                    setSelectedDecision={setSelectedDecision}
                    verifierId={verifierId}
                    setVerifierId={setVerifierId}
                    disputePreventedInput={disputePreventedInput}
                    setDisputePreventedInput={setDisputePreventedInput}
                    verifierNotes={verifierNotes}
                    setVerifierNotes={setVerifierNotes}
                    auditValidationError={auditValidationError}
                    setAuditValidationError={setAuditValidationError}
                    submittingAudit={submittingAudit}
                    onSubmit={handleSubmitAuditDecision}
                  />

                  <AuditHistoryTable
                    auditHistory={auditHistory}
                    onClearSession={handleClearAuditSession}
                  />
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
      <Footer />
    </div>
  );
}
