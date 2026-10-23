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
import { formatNarrativeText, formatRupiah, stripMarkdown } from '../../utils/formatters';

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
    (claim.risk_category === 'HIGH_RISK' ? 'REJECTED_UPCODING' : 'PENDING_CLARIFICATION');

  const formattedDecision = formatNarrativeText(effectiveDecision);

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

  // Copy Narrative handler
  const handleCopyNarrative = () => {
    if (!copilotData?.narrative) return;
    navigator.clipboard.writeText(stripMarkdown(copilotData.narrative));
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2200);
  };

  // Copy Letter handler
  const handleCopyLetter = () => {
    if (!copilotData?.letter) return;
    navigator.clipboard.writeText(stripMarkdown(copilotData.letter));
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
              Analisis narasi klinis Permenkes No. 26/2021 & draf korespondensi resmi rumah sakit berbasis Google Gemini (Free Tier)
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
              <div className="flex items-center gap-2 min-w-0">
                <FileText className="h-4 w-4 shrink-0 text-indigo-600 dark:text-indigo-400" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 sm:text-sm">
                  Telaah Narasi Klinis Permenkes No. 26/2021 & 16/2019
                </span>
              </div>

              {/* Action & Copy buttons appear here ONLY when narrative exists (No duplicate in empty state) */}
              {copilotData?.narrative && (
                <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                  <button
                    type="button"
                    onClick={handleGenerateNarrative}
                    disabled={loadingNarrative}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-indigo-700 cursor-pointer disabled:opacity-50"
                  >
                    {loadingNarrative ? (
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Sparkles className="h-3.5 w-3.5" />
                    )}
                    <span>{loadingNarrative ? 'Menganalisis...' : 'Perbarui Telaah'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyNarrative}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer"
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
                  Menganalisis kode ICD-10, aturan INA-CBG, dan metrik deviasi radar 5-sumbu...
                </p>
                <p className="text-[11px] text-slate-400">
                  Didukung model Google Gemini Flash Free Tier dengan sanitasi Zero-PII
                </p>
              </div>
            ) : copilotData?.narrative ? (
              <div className="mt-3 max-h-96 overflow-y-auto whitespace-pre-line rounded-lg bg-slate-50 p-3.5 font-sans text-xs leading-relaxed text-slate-800 dark:bg-slate-950/60 dark:text-slate-200">
                {stripMarkdown(copilotData.narrative)}
              </div>
            ) : (
              /* Single Centralized Call-to-Action (No double button!) */
              <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400 mb-3 shadow-xs">
                  <Sparkles className="h-6 w-6" />
                </div>
                <p className="text-xs font-medium text-slate-600 dark:text-slate-300 max-w-md">
                  Belum ada telaah narasi klinis untuk klaim{' '}
                  <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                    {claim.claim_id}
                  </span>
                  .
                </p>
                <p className="text-[11px] text-slate-400 mt-1 mb-4">
                  Analisis otomatis kode ICD-10, aturan INA-CBG, dan metrik deviasi radar 5-sumbu.
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
                  <span>{loadingNarrative ? 'Menganalisis Klinis AI...' : 'Susun Telaah Klinis'}</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Hospital Inquiry Letter Draft */}
        {activeTab === 'letter' && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            {/* Header: Title & Status on Left, Action & Copy Buttons on Right ONLY when content exists */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 border-b border-slate-100 pb-3 dark:border-slate-800">
              <div className="flex flex-wrap items-center gap-2 min-w-0">
                <FileText className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 sm:text-sm">
                  Draf Surat Klarifikasi Faskes
                </span>
                <span className="rounded bg-emerald-50 px-2 py-0.5 font-mono text-[10px] font-semibold text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
                  Status: {formattedDecision}
                </span>
                {disputeAmount > 0 && (
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    Selisih: {formatRupiah(disputeAmount)}
                  </span>
                )}
              </div>

              {/* Action & Single Copy button appear here ONLY when letter exists (No duplicate in empty state) */}
              {copilotData?.letter && (
                <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                  <button
                    type="button"
                    onClick={handleGenerateLetter}
                    disabled={loadingLetter}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 cursor-pointer disabled:opacity-50"
                  >
                    {loadingLetter ? (
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <FileText className="h-3.5 w-3.5" />
                    )}
                    <span>{loadingLetter ? 'Menyusun...' : 'Perbarui Draf Surat'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyLetter}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer"
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
                  Menyusun draf surat resmi korespondensi BPJS Kesehatan ke Direktur RS...
                </p>
                <p className="text-[11px] text-slate-400">
                  Memasukkan dasar hukum Permenkes No. 26/2021 & daftar bukti rekam medis
                </p>
              </div>
            ) : copilotData?.letter ? (
              <div className="mt-3">
                <div className="max-h-96 overflow-y-auto whitespace-pre-line rounded-lg border border-slate-200 bg-slate-50 p-4 font-mono text-xs leading-relaxed text-slate-800 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200">
                  {stripMarkdown(copilotData.letter)}
                </div>
                {/* Clean Footer note without duplicate copy button */}
                <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500">
                  <span>Format resmi siap cetak / ekspor ke portal e-Klaim Faskes</span>
                </div>
              </div>
            ) : (
              /* Single Centralized Call-to-Action (No double button!) */
              <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400 mb-3 shadow-xs">
                  <FileText className="h-6 w-6" />
                </div>
                <p className="text-xs font-medium text-slate-600 dark:text-slate-300 max-w-md">
                  Draf surat klarifikasi belum dibuat untuk klaim{' '}
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    {claim.claim_id}
                  </span>
                  .
                </p>
                <p className="text-[11px] text-slate-400 mt-1 mb-4">
                  Format surat resmi dinas BPJS Kesehatan ke Direktur RS dengan rincian berkas pendukung.
                </p>
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
                  <span>{loadingLetter ? 'Menyusun Draf Surat...' : 'Buat Draf Surat'}</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
