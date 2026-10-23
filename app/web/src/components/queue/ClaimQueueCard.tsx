import React from 'react';
import type { ClaimEvaluationResponse, VerifierDecision } from '../../types/jagaKode';
import {
  formatDecisionLabel,
  formatRiskLabel,
  formatRupiah,
  formatRuleLabel,
} from '../../utils/formatters';
import { RiskBadge } from '../common/RiskBadge';

interface ClaimQueueCardProps {
  item: ClaimEvaluationResponse;
  index: number;
  isSelected: boolean;
  auditStatus?: VerifierDecision;
  onSelect: () => void;
  onLoadToSimulator: () => void;
}

export const ClaimQueueCard: React.FC<ClaimQueueCardProps> = ({
  item,
  index,
  isSelected,
  auditStatus,
  onSelect,
  onLoadToSimulator,
}) => {
  const isHighRisk = item.risk_category === 'HIGH_RISK';
  const isMediumRisk = item.risk_category === 'MEDIUM_RISK';

  // Styling kartu terpilih dinamis selaras dengan tingkat risiko klaim
  const selectedThemeClass = isHighRisk
    ? 'border-rose-600 bg-rose-50/70 shadow-xs ring-1 ring-rose-500/30 dark:border-rose-500 dark:bg-rose-950/40'
    : isMediumRisk
    ? 'border-amber-500 bg-amber-50/70 shadow-xs ring-1 ring-amber-500/30 dark:border-amber-500 dark:bg-amber-950/40'
    : 'border-emerald-600 bg-emerald-50/70 shadow-xs ring-1 ring-emerald-500/30 dark:border-emerald-500 dark:bg-emerald-950/40';

  return (
    <div
      onClick={onSelect}
      className={`group flex flex-col gap-2.5 rounded-xl border p-3.5 transition-all cursor-pointer ${
        isSelected
          ? selectedThemeClass
          : 'border-slate-200/80 bg-white hover:border-slate-300 hover:shadow-xs dark:border-slate-800/90 dark:bg-slate-900/50 dark:hover:border-slate-700'
      }`}
    >
      <div className="flex items-start justify-between gap-2.5">
        <div className="flex items-start gap-2.5 min-w-0 flex-1">
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-200/80 font-mono text-[10px] font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300 mt-0.5">
            {index + 1}
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
          <RiskBadge category={item.risk_category} />
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
            onLoadToSimulator();
          }}
          className="shrink-0 text-[11px] font-semibold text-[#00529C] opacity-0 group-hover:opacity-100 hover:underline dark:text-sky-400 cursor-pointer"
        >
          Uji di Simulator →
        </button>
      </div>
    </div>
  );
};
