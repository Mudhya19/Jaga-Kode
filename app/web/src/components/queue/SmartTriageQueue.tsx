import React from 'react';
import { Layers, Search } from 'lucide-react';
import type {
  ClaimEvaluationResponse,
  RiskCategory,
  VerifierDecision,
} from '../../types/jagaKode';
import { ClaimQueueCard } from './ClaimQueueCard';

interface SmartTriageQueueProps {
  totalClaimsCount: number;
  filteredQueue: ClaimEvaluationResponse[];
  selectedClaimId: string;
  categoryFilter: 'ALL' | RiskCategory;
  setCategoryFilter: (filter: 'ALL' | RiskCategory) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  auditedClaimsMap: Record<string, VerifierDecision>;
  onSelectClaim: (claimId: string) => void;
  onLoadClaimToSimulator: (claim: ClaimEvaluationResponse) => void;
  kpiStats: {
    total: number;
    highCount: number;
    medCount: number;
    lowCount: number;
  };
}

export const SmartTriageQueue: React.FC<SmartTriageQueueProps> = ({
  totalClaimsCount,
  filteredQueue,
  selectedClaimId,
  categoryFilter,
  setCategoryFilter,
  searchQuery,
  setSearchQuery,
  auditedClaimsMap,
  onSelectClaim,
  onLoadClaimToSimulator,
  kpiStats,
}) => {
  return (
    <div className="lg:col-span-5 flex flex-col rounded-2xl border border-slate-200/90 bg-white shadow-xs dark:border-slate-800 dark:bg-[#111827] h-fit lg:self-start lg:sticky lg:top-20">
      <div className="border-b border-slate-200 p-4 dark:border-slate-800">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-[#00529C] dark:text-sky-400" />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              Smart Triage Queue (Antrean Berbasis Prioritas Risiko)
            </h2>
          </div>
          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            {filteredQueue.length} / {totalClaimsCount} Klaim
          </span>
        </div>

        {/* Filter Tabs (Background awal putih bersih, berubah warna sesuai status saat diklik/aktif) */}
        <div className="mt-3 flex flex-wrap gap-1.5">
          {(
            [
              {
                id: 'ALL',
                label: `Semua (${kpiStats.total})`,
                activeClass: 'bg-[#00529C] text-white border border-[#00529C] shadow-xs dark:bg-sky-600 dark:border-sky-600',
              },
              {
                id: 'HIGH_RISK',
                label: `High Risk (${kpiStats.highCount})`,
                activeClass: 'bg-rose-600 text-white border border-rose-600 shadow-xs dark:bg-rose-600 dark:border-rose-600',
              },
              {
                id: 'MEDIUM_RISK',
                label: `Medium (${kpiStats.medCount})`,
                activeClass: 'bg-amber-500 text-white border border-amber-500 shadow-xs dark:bg-amber-600 dark:border-amber-600',
              },
              {
                id: 'LOW_RISK',
                label: `Fast-Track (${kpiStats.lowCount})`,
                activeClass: 'bg-emerald-600 text-white border border-emerald-600 shadow-xs dark:bg-emerald-600 dark:border-emerald-600',
              },
            ] as const
          ).map((tab) => {
            const active = categoryFilter === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setCategoryFilter(tab.id)}
                className={`rounded-lg px-2.5 py-1 text-xs font-bold transition-all cursor-pointer ${
                  active
                    ? tab.activeClass
                    : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 dark:bg-slate-900 dark:text-slate-300 dark:border-slate-800 dark:hover:bg-slate-800'
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

      {/* Scrollable Claims Queue Cards (Auto-flex to content, max bounded to viewport) */}
      <div className="max-h-[calc(100vh-220px)] min-h-0 overflow-y-auto p-2.5 space-y-2.5">
        {filteredQueue.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 dark:text-slate-400">
            Tidak ada klaim yang cocok dengan filter atau kata kunci pencarian.
          </div>
        ) : (
          filteredQueue.map((item, idx) => (
            <ClaimQueueCard
              key={item.claim_id}
              item={item}
              index={idx}
              isSelected={selectedClaimId === item.claim_id}
              auditStatus={auditedClaimsMap[item.claim_id]}
              onSelect={() => onSelectClaim(item.claim_id)}
              onLoadToSimulator={() => onLoadClaimToSimulator(item)}
            />
          ))
        )}
      </div>
    </div>
  );
};
