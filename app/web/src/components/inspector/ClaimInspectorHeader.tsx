import React from 'react';
import { FileSearch } from 'lucide-react';
import type { ClaimEvaluationResponse, VerifierDecision } from '../../types/jagaKode';
import { formatDecisionLabel, formatRuleLabel } from '../../utils/formatters';
import { RiskBadge } from '../common/RiskBadge';

interface ClaimInspectorHeaderProps {
  claim: ClaimEvaluationResponse;
  auditDecision?: VerifierDecision;
}

export const ClaimInspectorHeader: React.FC<ClaimInspectorHeaderProps> = ({
  claim,
  auditDecision,
}) => {
  return (
    <div>
      {/* Header Info & Dual-Fusion Score */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#00529C] dark:text-sky-400">
              Claim Detail Inspector
            </span>
            <RiskBadge category={claim.risk_category} />
            {auditDecision && (
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-bold border ${
                  auditDecision === 'REJECTED_UPCODING'
                    ? 'bg-red-500/15 text-red-600 dark:bg-red-500/20 dark:text-red-400 border-red-500/30'
                    : auditDecision === 'PENDING_CLARIFICATION'
                    ? 'bg-amber-500/15 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300 border-amber-500/30'
                    : 'bg-emerald-500/15 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 border-emerald-500/30'
                }`}
              >
                Keputusan Verifikator: {formatDecisionLabel(auditDecision)}
              </span>
            )}
          </div>
          <h2 className="mt-1 font-mono text-lg font-extrabold text-slate-900 dark:text-white sm:text-xl">
            {claim.claim_id}
          </h2>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            INA-CBG:{' '}
            <strong className="font-mono text-slate-800 dark:text-slate-200">
              {claim.FKL19 || 'N/A'}
            </strong>{' '}
            • Diagnosis Primer:{' '}
            <strong className="font-mono text-slate-800 dark:text-slate-200">
              {claim.FKL17A || 'N/A'}
            </strong>{' '}
            ({claim.FKL18 || claim.FKL17A}) • Peer Group:{' '}
            <strong className="font-mono text-slate-800 dark:text-slate-200">
              {claim.peer_group_id || '4_1_3_1'}
            </strong>{' '}
            (CMG {claim.FKL20 ?? '-'})
          </p>
        </div>

        {/* Dual-Guardrail Score Pills */}
        <div className="flex flex-col items-end gap-1.5">
          <div
            className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 cursor-help"
            title="Formula Dual Risk Fusion: CPS = 0.55 × S_rule + 0.45 × S_anomaly (Disertai Hard-Fail Override untuk anomali ekstrim)"
          >
            Dual Risk Fusion:{' '}
            <span className="font-mono font-bold text-slate-700 dark:text-slate-200">
              CPS = 0.55 × S_rule + 0.45 × S_anomaly
            </span>
          </div>
          <div
            className="flex items-center gap-2.5"
            title="Dual Risk Fusion: Composite Priority Score (CPS) = 0.55 × S_rule + 0.45 × S_anomaly (Disertai Hard-Fail Override untuk anomali ekstrim)"
          >
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-center dark:border-slate-800 dark:bg-slate-900">
              <div className="text-[10px] font-semibold uppercase text-slate-500 dark:text-slate-400">
                Rule Score (55%)
              </div>
              <div className="font-mono text-sm font-extrabold text-slate-800 dark:text-slate-100">
                {claim.rule_risk_score.toFixed(1)}
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-center dark:border-slate-800 dark:bg-slate-900">
              <div className="text-[10px] font-semibold uppercase text-slate-500 dark:text-slate-400">
                ML Anomaly (45%)
              </div>
              <div className="font-mono text-sm font-extrabold text-slate-800 dark:text-slate-100">
                {claim.ml_anomaly_score.toFixed(1)}
              </div>
            </div>
            <div
              className="rounded-xl px-3.5 py-2 text-center text-white shadow-xs"
              style={{ backgroundColor: claim.badge_color }}
            >
              <div className="text-[10px] font-bold uppercase opacity-90">
                Composite CPS
              </div>
              <div className="font-mono text-base font-extrabold">
                {claim.risk_index.toFixed(1)}
              </div>
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
            {claim.recommended_action}
          </span>
          <div className="mt-1 text-[11px] text-slate-600 dark:text-slate-400">
            Faktor Pemicu Dominan:{' '}
            <code className="font-mono font-bold">{formatRuleLabel(claim.primary_driver)}</code>
          </div>
        </div>
      </div>
    </div>
  );
};
