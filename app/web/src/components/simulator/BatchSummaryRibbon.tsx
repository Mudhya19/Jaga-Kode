import React from 'react';
import type { BatchEvaluationSummary } from '../../types/jagaKode';
import { formatRupiah } from '../../utils/formatters';

interface BatchSummaryRibbonProps {
  summary: BatchEvaluationSummary | null;
  onClose: () => void;
}

export const BatchSummaryRibbon: React.FC<BatchSummaryRibbonProps> = ({
  summary,
  onClose,
}) => {
  if (!summary) return null;

  return (
    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-500/30 bg-emerald-50/10 px-4 py-2.5 text-xs dark:border-emerald-500/30 dark:bg-emerald-950/40">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-bold text-emerald-800 dark:text-emerald-300">
          Hasil Evaluasi Otomatis Batch Klaim:
        </span>
        <span>
          Total: <strong>{summary.total_claims} klaim</strong>
        </span>
        <span>•</span>
        <span className="text-red-600 dark:text-red-400 font-semibold">
          High Risk: {summary.high_risk_count}
        </span>
        <span>•</span>
        <span className="text-amber-600 dark:text-amber-400 font-semibold">
          Medium Risk: {summary.medium_risk_count}
        </span>
        <span>•</span>
        <span className="text-emerald-700 dark:text-emerald-300 font-semibold">
          Low Risk: {summary.low_risk_count} ({summary.fast_track_percentage}% Fast-Track)
        </span>
        <span>•</span>
        <span>
          Tagihan Batch: <strong>{formatRupiah(summary.total_billed_idr)}</strong>
        </span>
        <span>•</span>
        <span>
          Potensi Penghematan Dispute:{' '}
          <strong className="text-emerald-700 dark:text-emerald-300">
            {formatRupiah(summary.total_disputed_potential_idr)}
          </strong>
        </span>
      </div>
      <button
        type="button"
        onClick={onClose}
        className="text-xs font-semibold underline opacity-75 hover:opacity-100 cursor-pointer"
      >
        Sembunyikan
      </button>
    </div>
  );
};
