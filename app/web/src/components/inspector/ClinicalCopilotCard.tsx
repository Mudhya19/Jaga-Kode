import React, { useState, useEffect, useCallback } from 'react';
import {
  Sparkles,
  FileText,
  Copy,
  Check,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { jagaKodeApi } from '../../services/api';
import type {
  ClaimEvaluationResponse,
  CopilotExplainResponse,
  VerifierDecision,
} from '../../types/jagaKode';
import { formatNarrativeText, formatRupiah, cleanPlainTextForCopy } from '../../utils/formatters';

interface ClinicalCopilotCardProps {
  claim: ClaimEvaluationResponse;
  disputeAmount: number;
  auditDecision?: VerifierDecision;
  apiKey?: string;
  isDark?: boolean;
}

type ActiveCopilotTab = 'narrative' | 'letter';

export const ClinicalCopilotCard: React.FC<ClinicalCopilotCardProps> = ({
  claim,
  disputeAmount,
  auditDecision,
  apiKey,
}) => {
  const [activeTab, setActiveTab] = useState<ActiveCopilotTab>('narrative');

  // Generation state
  const [loadingNarrative, setLoadingNarrative] = useState<boolean>(false);
  const [loadingLetter, setLoadingLetter] = useState<boolean>(false);
  const [copilotData, setCopilotData] = useState<CopilotExplainResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Copy feedback state
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);
  const [copiedLetter, setCopiedLetter] = useState<boolean>(false);

  const effectiveDecision =
    auditDecision ||
    (claim.risk_category === 'HIGH_RISK'
      ? 'REJECTED_UPCODING'
      : claim.risk_category === 'LOW_RISK'
      ? 'APPROVED'
      : 'PENDING_CLARIFICATION');

  const formattedDecision = formatNarrativeText(effectiveDecision);

  const isHighRisk =
    effectiveDecision === 'REJECTED_UPCODING' || claim.risk_category === 'HIGH_RISK';
  const isMediumRisk =
    effectiveDecision === 'PENDING_CLARIFICATION' || claim.risk_category === 'MEDIUM_RISK';
  const isLowRisk = !isHighRisk && !isMediumRisk;

  // Status badge styling (dynamic based on risk)
  const statusBadgeClass = isHighRisk
    ? 'bg-red-500/15 text-red-700 dark:bg-red-500/20 dark:text-red-300 border-red-500/30'
    : isMediumRisk
    ? 'bg-amber-500/15 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300 border-amber-500/30'
    : 'bg-emerald-500/15 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 border-emerald-500/30';

  // SEP / Claim ID text highlight (dynamic based on risk)
  const sepColorClass = isHighRisk
    ? 'text-red-600 dark:text-red-400'
    : isMediumRisk
    ? 'text-amber-600 dark:text-amber-400'
    : 'text-emerald-600 dark:text-emerald-400';

  const getEnrichedClaim = useCallback(() => {
    return {
      ...(claim as unknown as Record<string, unknown>),
      decision: effectiveDecision,
      audit_decision: effectiveDecision,
    };
  }, [claim, effectiveDecision]);

  // Reset when selected claim changes
  useEffect(() => {
    setCopilotData(null);
    setErrorMessage(null);
  }, [claim.claim_id]);

  // Generate Narrative
  const handleGenerateNarrative = async () => {
    setLoadingNarrative(true);
    setErrorMessage(null);
    try {
      const res = await jagaKodeApi.explainWithCopilot(
        {
          claim_data: getEnrichedClaim(),
          dispute_prevented_idr: disputeAmount,
          include_narrative: true,
          include_letter: Boolean(copilotData?.letter),
        },
        apiKey
      );
      setCopilotData((prev) => ({
        ...res,
        letter: res.letter || prev?.letter || null,
      }));
      setActiveTab('narrative');
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Gagal menghasilkan telaah narasi klinis.'
      );
    } finally {
      setLoadingNarrative(false);
    }
  };

  // Generate Letter
  const handleGenerateLetter = async () => {
    setLoadingLetter(true);
    setErrorMessage(null);
    try {
      const res = await jagaKodeApi.explainWithCopilot(
        {
          claim_data: getEnrichedClaim(),
          dispute_prevented_idr: disputeAmount,
          include_narrative: Boolean(copilotData?.narrative),
          include_letter: true,
        },
        apiKey
      );
      setCopilotData((prev) => ({
        ...res,
        narrative: res.narrative || prev?.narrative || null,
      }));
      setActiveTab('letter');
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Gagal menyusun draf surat klarifikasi.'
      );
    } finally {
      setLoadingLetter(false);
    }
  };

  // Reset individual tabs to clean empty state (Refresh handler)
  const handleResetNarrative = () => {
    setCopilotData((prev) => (prev ? { ...prev, narrative: null } : null));
    setErrorMessage(null);
  };

  const handleResetLetter = () => {
    setCopilotData((prev) => (prev ? { ...prev, letter: null } : null));
    setErrorMessage(null);
  };

  // Copy Narrative handler (clean plain text ready for Word/Notepad/Chat)
  const handleCopyNarrative = () => {
    if (!copilotData?.narrative) return;
    navigator.clipboard.writeText(cleanPlainTextForCopy(copilotData.narrative));
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2200);
  };

  // Copy Letter handler (clean plain text ready for Word/Notepad/Chat)
  const handleCopyLetter = () => {
    if (!copilotData?.letter) return;
    navigator.clipboard.writeText(cleanPlainTextForCopy(copilotData.letter));
    setCopiedLetter(true);
    setTimeout(() => setCopiedLetter(false), 2200);
  };

  return (
    <div className="mt-4 rounded-xl border border-indigo-200/80 bg-gradient-to-b from-indigo-50/40 via-white to-slate-50/80 p-4 shadow-sm dark:border-indigo-900/40 dark:from-indigo-950/20 dark:via-slate-900 dark:to-slate-900">
      {/* Top Header Banner & Tab Switcher (Responsive Flex Layout) */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-indigo-100 pb-3 dark:border-indigo-950/60">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-600 text-white shadow-xs">
            <Sparkles className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-extrabold text-slate-900 dark:text-white sm:text-base">
                AI Clinical Copilot & Draf Surat Klarifikasi Faskes
              </h3>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 font-mono text-[10px] font-bold text-emerald-700 dark:text-emerald-300">
                <ShieldCheck className="h-3 w-3" />
                Zero-PII UU No. 27/2022
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Analisis narasi klinis Permenkes No. 26/2021 & draf korespondensi resmi rumah sakit
            </p>
          </div>
        </div>

        {/* 2 Clean Tab Switchers */}
        <div className="flex self-start sm:self-auto shrink-0 rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-xs font-medium dark:border-slate-800 dark:bg-slate-950">
          <button
            type="button"
            onClick={() => setActiveTab('narrative')}
            className={`rounded-md px-3.5 py-1.5 transition-all cursor-pointer ${
              activeTab === 'narrative'
                ? 'bg-white font-bold text-indigo-700 shadow-xs dark:bg-slate-900 dark:text-indigo-400'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-300'
            }`}
          >
            Telaah Narasi Permenkes
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('letter')}
            className={`rounded-md px-3.5 py-1.5 transition-all cursor-pointer ${
              activeTab === 'letter'
                ? 'bg-white font-bold text-emerald-700 shadow-xs dark:bg-slate-900 dark:text-emerald-400'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-300'
            }`}
          >
            Draf Surat Klarifikasi
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-red-50 p-2.5 text-xs text-red-700 dark:bg-red-950/40 dark:text-red-300">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Content Area */}
      <div className="mt-3">
        {/* TAB 1: Clinical Narrative */}
        {activeTab === 'narrative' && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            {/* Header: Title on Left, Action & Copy Buttons on Right ONLY when content exists */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 border-b border-slate-100 pb-3 dark:border-slate-800">
              <div className="flex flex-wrap items-center gap-2 min-w-0">
                <FileText className="h-4 w-4 shrink-0 text-indigo-600 dark:text-indigo-400" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 sm:text-sm">
                  Telaah Narasi Klinis Permenkes No. 26/2021 & 16/2019
                </span>
                <span
                  className={`rounded px-2 py-0.5 font-mono text-[10px] font-semibold border ${
                    isHighRisk
                      ? 'bg-red-500/15 text-red-700 dark:bg-red-500/20 dark:text-red-300 border-red-500/30'
                      : isMediumRisk
                      ? 'bg-amber-500/15 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300 border-amber-500/30'
                      : 'bg-emerald-500/15 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 border-emerald-500/30'
                  }`}
                >
                  {isHighRisk
                    ? 'Risiko Tinggi (Reject Upcoding)'
                    : isMediumRisk
                    ? 'Risiko Sedang (Pending Clarification)'
                    : 'Risiko Rendah (Approved / Fast-Track)'}
                </span>
              </div>

              {/* Header Actions: Refresh & Copy buttons (Visible when narrative exists) */}
              {copilotData?.narrative && (
                <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                  <button
                    type="button"
                    onClick={handleResetNarrative}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer"
                    title="Kosongkan tampilan untuk memulai telaah baru"
                  >
                    <RefreshCw className="h-3.5 w-3.5 text-indigo-600" />
                    <span>Refresh</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyNarrative}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer"
                    title="Salin teks telaah klinis"
                  >
                    {copiedNarrative ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-emerald-600" />
                        <span className="text-emerald-600 font-bold">Tersalin!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        <span>Salin</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>

            {loadingNarrative ? (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <RefreshCw className="h-6 w-6 animate-spin text-indigo-600" />
                <p className="mt-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Sedang menganalisis kesesuaian klinis dengan regulasi INA-CBG...
                </p>
                <p className="text-[11px] text-slate-400">
                  Memverifikasi kaidah koding diagnosis utama, komorbiditas, dan deviasi biaya kelompok sejenis
                </p>
              </div>
            ) : copilotData?.narrative ? (
              <div className="mt-3 max-h-96 overflow-y-auto whitespace-pre-line rounded-lg bg-slate-50 p-3.5 font-sans text-xs leading-relaxed text-slate-800 dark:bg-slate-950/60 dark:text-slate-200">
                {cleanPlainTextForCopy(copilotData.narrative)}
              </div>
            ) : (
              /* Single Centralized Call-to-Action in Empty State */
              <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400 mb-3 shadow-xs">
                  <Sparkles className="h-6 w-6" />
                </div>
                <p className="text-xs font-medium text-slate-600 dark:text-slate-300 max-w-md">
                  Belum ada telaah narasi klinis untuk berkas klaim{' '}
                  <span className={`font-mono font-bold ${sepColorClass}`}>
                    {claim.claim_id}
                  </span>
                  .
                </p>
                <p className="text-[11px] text-slate-400 mt-1 mb-4">
                  Pemeriksaan kesesuaian diagnosis, prosedur tindakan, dan indikator kepatuhan Permenkes No. 26/2021 & 16/2019.
                </p>
                <button
                  type="button"
                  onClick={handleGenerateNarrative}
                  disabled={loadingNarrative}
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-indigo-700 cursor-pointer disabled:opacity-50 transition-all hover:scale-[1.02]"
                >
                  {loadingNarrative ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                  <span>{loadingNarrative ? 'Sedang Menganalisis...' : 'Susun Telaah Klinis'}</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Hospital Inquiry Letter Draft */}
        {activeTab === 'letter' && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            {/* Header: Title & Status on Left, Refresh & Copy Buttons on Right ONLY when content exists */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 border-b border-slate-100 pb-3 dark:border-slate-800">
              <div className="flex flex-wrap items-center gap-2 min-w-0">
                {/* Logo draf hijau zamrud statis */}
                <FileText className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 sm:text-sm">
                  {isLowRisk ? 'Draf Surat Persetujuan (Fast-Track)' : 'Draf Surat Klarifikasi Faskes'}
                </span>
                {/* Status Badge dinamis sesuai risiko */}
                <span className={`rounded px-2 py-0.5 font-mono text-[10px] font-semibold border ${statusBadgeClass}`}>
                  Status: {isLowRisk ? 'Approved (Fast-Track)' : isHighRisk ? 'Reject Upcoding' : 'Pending Clarification'}
                </span>
                {disputeAmount > 0 && !isLowRisk && (
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    Selisih: {formatRupiah(disputeAmount)}
                  </span>
                )}
              </div>

              {/* Header Actions: Refresh & Copy buttons (Visible when letter exists) */}
              {copilotData?.letter && (
                <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                  <button
                    type="button"
                    onClick={handleResetLetter}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer"
                    title="Kosongkan tampilan untuk memulai draf baru"
                  >
                    <RefreshCw className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Refresh</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyLetter}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer"
                    title="Salin teks surat resmi"
                  >
                    {copiedLetter ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-emerald-600" />
                        <span className="text-emerald-600 font-bold">Tersalin!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        <span>Salin</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>

            {loadingLetter ? (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <RefreshCw className="h-6 w-6 animate-spin text-emerald-600" />
                <p className="mt-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Sedang menyusun naskah dinas resmi untuk Rumah Sakit...
                </p>
                <p className="text-[11px] text-slate-400">
                  Memasukkan dasar hukum Permenkes No. 26/2021 dan rincian berkas rekam medis yang diperlukan
                </p>
              </div>
            ) : copilotData?.letter ? (
              <div className="mt-3">
                <div className="max-h-96 overflow-y-auto whitespace-pre-line rounded-lg border border-slate-200 bg-slate-50 p-4 font-mono text-xs leading-relaxed text-slate-800 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200">
                  {cleanPlainTextForCopy(copilotData.letter)}
                </div>
              </div>
            ) : (
              /* Single Centralized Call-to-Action in Empty State */
              <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
                {/* Logo container hijau zamrud statis */}
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400 mb-3 shadow-xs">
                  <FileText className="h-6 w-6" />
                </div>
                <p className="text-xs font-medium text-slate-600 dark:text-slate-300 max-w-md">
                  Belum ada draf surat korespondensi untuk berkas klaim{' '}
                  <span className={`font-mono font-bold ${sepColorClass}`}>
                    {claim.claim_id}
                  </span>
                  .
                </p>
                <p className="text-[11px] text-slate-400 mt-1 mb-4">
                  {isLowRisk
                    ? 'Klaim memenuhi ketentuan persetujuan cepat (Fast-Track). Surat penetapan persetujuan siap diterbitkan.'
                    : isHighRisk
                    ? 'Klaim terindikasi ketidaksesuaian koding atau upcoding. Surat resmi penetapan koreksi tarif dan konfirmasi ke pihak Rumah Sakit.'
                    : 'Klaim memerlukan konfirmasi kelengkapan berkas medis dan klarifikasi ke pihak Rumah Sakit.'}
                </p>
                {/* Button draf hijau zamrud statis */}
                <button
                  type="button"
                  onClick={handleGenerateLetter}
                  disabled={loadingLetter}
                  className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-emerald-700 cursor-pointer disabled:opacity-50 transition-all hover:scale-[1.02]"
                >
                  {loadingLetter ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <FileText className="h-4 w-4" />
                  )}
                  <span>
                    {loadingLetter
                      ? 'Sedang Menyusun Surat...'
                      : isLowRisk
                      ? 'Buat Surat Persetujuan'
                      : isHighRisk
                      ? 'Buat Surat Koreksi'
                      : 'Buat Draf Surat'}
                  </span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
