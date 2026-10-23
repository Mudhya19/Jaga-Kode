import React from 'react';
import { History } from 'lucide-react';
import type { AuditRecordItem } from '../../types/jagaKode';
import { formatDecisionLabel, formatRupiah } from '../../utils/formatters';

interface AuditHistoryTableProps {
  auditHistory: AuditRecordItem[];
  onClearSession: () => void;
}

export const AuditHistoryTable: React.FC<AuditHistoryTableProps> = ({
  auditHistory,
  onClearSession,
}) => {
  return (
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
              onClick={onClearSession}
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
                  Belum ada rekaman jejak audit. Silakan kirim keputusan verifikasi di atas.
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
  );
};
