import React, { useState, useEffect, useCallback } from 'react';
import {
  Sparkles,
  FileText,
  Copy,
  Check,
  Send,
  ShieldCheck,
  MessageSquare,
  Key,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  Cpu,
} from 'lucide-react';
import { jagaKodeApi } from '../../services/api';
import type {
  ClaimEvaluationResponse,
  ChatMessageItem,
  CopilotExplainResponse,
  CopilotStatusResponse,
  VerifierDecision,
} from '../../types/jagaKode';
import { formatRupiah } from '../../utils/formatters';

interface ClinicalCopilotCardProps {
  claim: ClaimEvaluationResponse;
  disputeAmount: number;
  auditDecision?: VerifierDecision;
  apiKey?: string;
  isDark?: boolean;
}

type ActiveCopilotTab = 'narrative' | 'letter' | 'chat';

export const ClinicalCopilotCard: React.FC<ClinicalCopilotCardProps> = ({
  claim,
  disputeAmount,
  auditDecision,
  apiKey,
}) => {
  const [activeTab, setActiveTab] = useState<ActiveCopilotTab>('narrative');

  // Custom Gemini Key State
  const [geminiApiKey, setGeminiApiKey] = useState<string>(() => {
    return localStorage.getItem('jaga_kode_gemini_key') || '';
  });
  const [showKeyInput, setShowKeyInput] = useState<boolean>(false);
  const [copilotStatus, setCopilotStatus] = useState<CopilotStatusResponse | null>(null);

  // Generation state
  const [loadingNarrative, setLoadingNarrative] = useState<boolean>(false);
  const [loadingLetter, setLoadingLetter] = useState<boolean>(false);
  const [copilotData, setCopilotData] = useState<CopilotExplainResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Copy state
  const [copiedNarrative, setCopiedNarrative] = useState<boolean>(false);
  const [copiedLetter, setCopiedLetter] = useState<boolean>(false);

  // Chat Q&A state
  const [chatPrompt, setChatPrompt] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<ChatMessageItem[]>([]);
  const [sendingChat, setSendingChat] = useState<boolean>(false);

  const getEnrichedClaim = useCallback(() => {
    return {
      ...(claim as unknown as Record<string, unknown>),
      decision: auditDecision || (claim.risk_category === 'HIGH_RISK' ? 'REJECTED_UPCODING' : 'PENDING_CLARIFICATION'),
      audit_decision: auditDecision || (claim.risk_category === 'HIGH_RISK' ? 'REJECTED_UPCODING' : 'PENDING_CLARIFICATION'),
    };
  }, [claim, auditDecision]);

  // Check copilot status on mount or key change
  const refreshStatus = useCallback(() => {
    jagaKodeApi
      .getCopilotStatus(apiKey, geminiApiKey)
      .then((res) => setCopilotStatus(res))
      .catch(() => {
        setCopilotStatus({
          status: 'DEGRADED_OFFLINE_RULES_ONLY',
          configured: false,
          model: 'jaga_kode_deterministic_v2',
          zero_pii: true,
        });
      });
  }, [apiKey, geminiApiKey]);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  // Reset when claim changes
  useEffect(() => {
    setCopilotData(null);
    setErrorMessage(null);
    setChatHistory([]);
  }, [claim.claim_id]);

  const handleSaveKey = () => {
    localStorage.setItem('jaga_kode_gemini_key', geminiApiKey);
    refreshStatus();
    setShowKeyInput(false);
  };

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
          gemini_api_key: geminiApiKey || undefined,
        },
        apiKey,
        geminiApiKey
      );
      setCopilotData((prev) => ({
        ...res,
        letter: res.letter || prev?.letter || null,
      }));
      setActiveTab('narrative');
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Gagal menghasilkan telaah klinis copilot.'
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
          gemini_api_key: geminiApiKey || undefined,
        },
        apiKey,
        geminiApiKey
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

  // Copy Narrative
  const handleCopyNarrative = () => {
    if (!copilotData?.narrative) return;
    navigator.clipboard.writeText(copilotData.narrative);
    setCopiedNarrative(true);
    setTimeout(() => setCopiedNarrative(false), 2500);
  };

  // Copy Letter
  const handleCopyLetter = () => {
    if (!copilotData?.letter) return;
    navigator.clipboard.writeText(copilotData.letter);
    setCopiedLetter(true);
    setTimeout(() => setCopiedLetter(false), 2500);
  };

  // Send Chat message
  const handleSendChat = async (promptToSend?: string) => {
    const text = (promptToSend || chatPrompt).trim();
    if (!text || sendingChat) return;

    const newHistory: ChatMessageItem[] = [
      ...chatHistory,
      { role: 'user', text },
    ];
    setChatHistory(newHistory);
    setChatPrompt('');
    setSendingChat(true);

    try {
      const res = await jagaKodeApi.askCopilot(
        {
          claim_data: getEnrichedClaim(),
          prompt: text,
          history: chatHistory,
          gemini_api_key: geminiApiKey || undefined,
        },
        apiKey,
        geminiApiKey
      );
      setChatHistory([...newHistory, { role: 'model', text: res.reply }]);
    } catch (err) {
      setChatHistory([
        ...newHistory,
        {
          role: 'model',
          text: `Gagal memperoleh jawaban: ${
            err instanceof Error ? err.message : 'Kesalahan jaringan'
          }`,
        },
      ]);
    } finally {
      setSendingChat(false);
    }
  };

  return (
    <div className="mt-4 rounded-xl border border-indigo-200/80 bg-gradient-to-b from-indigo-50/40 via-white to-slate-50/80 p-4 shadow-sm dark:border-indigo-900/40 dark:from-indigo-950/20 dark:via-slate-900 dark:to-slate-900">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-indigo-100 pb-3 dark:border-indigo-950/60">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-600 text-white shadow-sm">
            <Sparkles className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
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

        {/* Status Pill & Key Config */}
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold ${
              copilotStatus?.status === 'ONLINE'
                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                : 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300'
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>
              {copilotStatus?.status === 'ONLINE'
                ? `Online (${copilotStatus.model || 'Gemini Flash Free'})`
                : 'Aturan Deterministik Lokal'}
            </span>
          </span>

          <button
            type="button"
            onClick={() => setShowKeyInput(!showKeyInput)}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer"
            title="Konfigurasi Google Gemini API Key"
          >
            <Key className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
            <span className="hidden sm:inline">Kunci Gemini</span>
          </button>
        </div>
      </div>

      {/* Expandable Gemini Key Config Bar */}
      {showKeyInput && (
        <div className="mt-3 rounded-lg border border-indigo-100 bg-indigo-50/70 p-3 text-xs dark:border-indigo-900/60 dark:bg-indigo-950/40">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-semibold text-slate-700 dark:text-slate-200">
              Google Gemini API Key (Free Tier 15 RPM / 1.500 RPD — Tanpa Kartu Kredit):
            </span>
            <span className="text-[11px] text-slate-500">
              Tersimpan aman di browser (Header X-Gemini-API-Key)
            </span>
          </div>
          <div className="mt-2 flex gap-2">
            <input
              type="password"
              value={geminiApiKey}
              onChange={(e) => setGeminiApiKey(e.target.value)}
              placeholder="Masukkan API Key (AQ.Ab8RN6Ju... atau AIzaSy...)"
              className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 font-mono text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
            <button
              type="button"
              onClick={handleSaveKey}
              className="rounded-md bg-indigo-600 px-3 py-1.5 font-bold text-white hover:bg-indigo-700 cursor-pointer"
            >
              Simpan
            </button>
          </div>
        </div>
      )}

      {/* Action Buttons Row: 1-Click Generate Narrative & Letter */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleGenerateNarrative}
            disabled={loadingNarrative}
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-bold text-white shadow-xs hover:bg-indigo-700 cursor-pointer disabled:opacity-50"
          >
            {loadingNarrative ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            <span>
              {loadingNarrative
                ? 'Menganalisis Klinis AI...'
                : '1-Klik Susun Telaah Klinis AI'}
            </span>
          </button>

          <button
            type="button"
            onClick={handleGenerateLetter}
            disabled={loadingLetter}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-2 text-xs font-bold text-white shadow-xs hover:bg-emerald-700 cursor-pointer disabled:opacity-50"
          >
            {loadingLetter ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <FileText className="h-3.5 w-3.5" />
            )}
            <span>
              {loadingLetter
                ? 'Menyusun Draf Surat...'
                : '1-Klik Buat Draf Surat Klarifikasi'}
            </span>
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-xs font-medium dark:border-slate-700 dark:bg-slate-800">
          <button
            type="button"
            onClick={() => setActiveTab('narrative')}
            className={`rounded-md px-3 py-1 transition-all cursor-pointer ${
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
            className={`rounded-md px-3 py-1 transition-all cursor-pointer ${
              activeTab === 'letter'
                ? 'bg-white font-bold text-emerald-700 shadow-xs dark:bg-slate-900 dark:text-emerald-400'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-300'
            }`}
          >
            Draf Surat Klarifikasi
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('chat')}
            className={`rounded-md px-3 py-1 transition-all cursor-pointer ${
              activeTab === 'chat'
                ? 'bg-white font-bold text-indigo-700 shadow-xs dark:bg-slate-900 dark:text-indigo-400'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-300'
            }`}
          >
            Copilot Q&A
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
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  Telaah Narasi Medis-Klinis (Permenkes No. 26/2021 & 16/2019)
                </span>
                {copilotData?.source && (
                  <span className="rounded bg-indigo-50 px-2 py-0.5 font-mono text-[10px] text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300">
                    Sumber: {copilotData.source} ({copilotData.model})
                  </span>
                )}
              </div>

              {copilotData?.narrative && (
                <button
                  type="button"
                  onClick={handleCopyNarrative}
                  className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer"
                >
                  {copiedNarrative ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-600" />
                      <span className="text-emerald-600">Tersalin!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Salin Telaah</span>
                    </>
                  )}
                </button>
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
                {copilotData.narrative}
              </div>
            ) : (
              <div className="py-8 text-center">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Belum ada telaah klinis terbuat untuk klaim{' '}
                  <code className="font-mono font-bold text-indigo-600">
                    {claim.claim_id}
                  </code>
                  .
                </p>
                <button
                  type="button"
                  onClick={handleGenerateNarrative}
                  className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-indigo-700 cursor-pointer"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Susun Telaah Klinis AI Sekarang</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Hospital Inquiry Letter Draft */}
        {activeTab === 'letter' && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  Draf Resmi Surat {auditDecision === 'REJECTED_UPCODING' ? 'Penetapan Koreksi Upcoding' : 'Klarifikasi / Konfirmasi Klaim'} ke FKRTL
                </span>
                <span className="rounded bg-emerald-50 px-2 py-0.5 font-mono text-[10px] text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
                  Status: {auditDecision || (claim.risk_category === 'HIGH_RISK' ? 'REJECTED_UPCODING' : 'PENDING_CLARIFICATION')} | Selisih: {formatRupiah(disputeAmount || 0)}
                </span>
              </div>

              {copilotData?.letter && (
                <button
                  type="button"
                  onClick={handleCopyLetter}
                  className="inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-3 py-1 text-xs font-bold text-white shadow-xs hover:bg-emerald-700 cursor-pointer"
                >
                  {copiedLetter ? (
                    <>
                      <Check className="h-3.5 w-3.5" />
                      <span>Surat Berhasil Disalin!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>1-Klik Salin Surat</span>
                    </>
                  )}
                </button>
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
                  {copilotData.letter}
                </div>
                <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500">
                  <span>Format siap cetak / ekspor ke portal e-Klaim Faskes</span>
                  <button
                    type="button"
                    onClick={handleCopyLetter}
                    className="inline-flex items-center gap-1 text-emerald-600 hover:underline font-semibold cursor-pointer"
                  >
                    <Copy className="h-3 w-3" />
                    <span>Salin Teks Lengkap Surat</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Draf surat klarifikasi belum dibuat. Cocok untuk status klaim{' '}
                  <span className="font-semibold text-amber-600">
                    PENDING CLARIFICATION
                  </span>{' '}
                  atau{' '}
                  <span className="font-semibold text-red-600">
                    REJECTED UPCODING
                  </span>
                  .
                </p>
                <button
                  type="button"
                  onClick={handleGenerateLetter}
                  className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-emerald-700 cursor-pointer"
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span>Buat Draf Surat Klarifikasi Sekarang</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: Interactive Copilot Chat */}
        {activeTab === 'chat' && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  Tanya-Jawab Klinis Verifikator (Interactive Copilot Q&A)
                </span>
              </div>
              <span className="text-[11px] text-slate-400">
                Konteks: {claim.claim_id} ({claim.FKL17A} / {claim.FKL19})
              </span>
            </div>

            {/* Quick Prompt Suggestions */}
            <div className="mt-3 flex flex-wrap gap-1.5">
              <span className="text-[11px] font-medium text-slate-400 self-center">
                Contoh:
              </span>
              {[
                'Apa aturan Permenkes terkait klaim ini?',
                'Berapa potensi selisih dispute rupiah?',
                'Dokumen rekam medis apa yang wajib diperiksa?',
                'Apakah severity jump ini wajar untuk LoS 1 hari?',
              ].map((suggestion, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSendChat(suggestion)}
                  disabled={sendingChat}
                  className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:border-indigo-400 hover:bg-indigo-50/50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 cursor-pointer disabled:opacity-50"
                >
                  {suggestion}
                </button>
              ))}
            </div>

            {/* Chat History Messages Stream */}
            <div className="mt-3 max-h-72 min-h-36 space-y-2.5 overflow-y-auto rounded-lg bg-slate-50 p-3 dark:bg-slate-950/60">
              {chatHistory.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-400">
                  <HelpCircle className="mx-auto mb-1 h-5 w-5 opacity-40" />
                  <span>
                    Belum ada percakapan. Tanyakan kaidah koding ICD-10, evaluasi tarif INA-CBG, atau regulasi Permenkes pada form di bawah.
                  </span>
                </div>
              ) : (
                chatHistory.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex flex-col ${
                      msg.role === 'user' ? 'items-end' : 'items-start'
                    }`}
                  >
                    <span className="text-[10px] font-bold text-slate-400 mb-0.5">
                      {msg.role === 'user' ? 'Verifikator BPJS' : 'Copilot Klinis AI'}
                    </span>
                    <div
                      className={`max-w-[85%] rounded-xl p-3 text-xs leading-relaxed whitespace-pre-line ${
                        msg.role === 'user'
                          ? 'bg-indigo-600 text-white rounded-br-none shadow-xs'
                          : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none dark:bg-slate-800 dark:text-slate-100 dark:border-slate-700 shadow-xs'
                      }`}
                    >
                      {msg.text}
                    </div>
                  </div>
                ))
              )}
              {sendingChat && (
                <div className="flex items-center gap-2 text-xs text-indigo-600 dark:text-indigo-400">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Copilot sedang menganalisis regulasi & merespons...</span>
                </div>
              )}
            </div>

            {/* Chat Input */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendChat();
              }}
              className="mt-2.5 flex gap-2"
            >
              <input
                type="text"
                value={chatPrompt}
                onChange={(e) => setChatPrompt(e.target.value)}
                placeholder="Ajukan pertanyaan klinis seputar klaim ini..."
                disabled={sendingChat}
                className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={sendingChat || !chatPrompt.trim()}
                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 cursor-pointer disabled:opacity-50"
              >
                <Send className="h-3.5 w-3.5" />
                <span>Kirim</span>
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
