import React, { useState } from 'react';
import {
  Check,
  CheckCircle2,
  Clock,
  Send,
  Sparkles,
  UserCheck,
  XCircle,
} from 'lucide-react';
import { QUICK_NOTE_TEMPLATES } from '../../constants/clinicalRules';
import type { ClaimEvaluationResponse, VerifierDecision } from '../../types/jagaKode';
import { buildVerifierClinicalNote, formatDecisionLabel } from '../../utils/formatters';

interface HumanInTheLoopAuditProps {
  claim?: ClaimEvaluationResponse | null;
  selectedDecision: VerifierDecision;
  setSelectedDecision: (decision: VerifierDecision) => void;
  verifierId: string;
  setVerifierId: (id: string) => void;
  disputePreventedInput: number;
  setDisputePreventedInput: (val: number) => void;
  verifierNotes: string;
  setVerifierNotes: (notes: string) => void;
  auditValidationError: string | null;
  setAuditValidationError: (err: string | null) => void;
  submittingAudit: boolean;
  onSubmit: (e: React.FormEvent) => void;
}

export const HumanInTheLoopAudit: React.FC<HumanInTheLoopAuditProps> = ({
  claim,
  selectedDecision,
  setSelectedDecision,
  verifierId,
  setVerifierId,
  disputePreventedInput,
  setDisputePreventedInput,
  verifierNotes,
  setVerifierNotes,
  auditValidationError,
  setAuditValidationError,
  submittingAudit,
  onSubmit,
}) => {
  const [isGenerated, setIsGenerated] = useState(false);

  const handleGenerateNotes = () => {
    const note = buildVerifierClinicalNote(claim, selectedDecision, disputePreventedInput);
    setVerifierNotes(note);
    if (auditValidationError) setAuditValidationError(null);
    setIsGenerated(true);
    setTimeout(() => setIsGenerated(false), 2000);
  };
  return (
    <div>
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

      <form onSubmit={onSubmit} className="mt-4 space-y-4">
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

        {/* Quick Clinical Note Templates & Generator */}
        <div>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Catatan Medis Verifikator (Wajib Diisi — Tersimpan di Audit Trail) *
            </label>
            <button
              type="button"
              onClick={handleGenerateNotes}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-indigo-700 transition-all cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
              title="Buat catatan telaah medis verifikator otomatis sesuai konteks klaim dan keputusan untuk dikirim"
            >
              {isGenerated ? (
                <>
                  <Check className="h-3.5 w-3.5" />
                  <span>Catatan Terisi!</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Generate Catatan</span>
                </>
              )}
            </button>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] text-slate-500 dark:text-slate-400 mr-1">
              Atau gunakan template SOP:
            </span>
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
                  SOP #{i + 1}
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
            placeholder="Tuliskan hasil pemeriksaan resume medis, bukti laboratorium, atau klik 'Generate Catatan' di atas..."
            className="mt-2 w-full rounded-xl border border-slate-300 bg-white p-3 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
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
    </div>
  );
};
