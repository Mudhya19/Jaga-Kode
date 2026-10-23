import React from 'react';
import {
  Award,
  CheckCircle2,
  Database,
  ShieldAlert,
  TrendingUp,
  Wallet,
  Zap,
} from 'lucide-react';
import { formatRupiah } from '../../utils/formatters';

export interface KpiSummaryStats {
  total: number;
  totalBilled: number;
  lowCount: number;
  highCount: number;
  medCount: number;
  fastTrackPct: number;
  potentialDisputeIdr: number;
  highRiskBilled: number;
  confirmedAuditSavingsIdr: number;
}

interface ExecutiveKpiBannerProps {
  kpiStats: KpiSummaryStats;
  runningBatch: boolean;
  onRunBatchSimulation: () => void;
}

export const ExecutiveKpiBanner: React.FC<ExecutiveKpiBannerProps> = ({
  kpiStats,
  runningBatch,
  onRunBatchSimulation,
}) => {
  return (
    <section
      aria-label="Executive KPI & Financial Impact Simulator"
      className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-[#111827] sm:p-5"
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00529C]/10 text-[#00529C] dark:bg-sky-500/20 dark:text-sky-400">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white sm:text-base">
              Executive KPI & Simulasi Dampak Finansial Dana Jaminan Sosial (DJS)
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Ringkasan triase real-time antrean FKRTL & kalkulasi potensi penghematan pencegahan upcoding
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300">
            <Award className="h-3.5 w-3.5" />
            Precision@100: 100.0% • PR-AUC: 0.9339 • Lift@5%: 8.05x
          </span>
          <button
            type="button"
            onClick={onRunBatchSimulation}
            disabled={runningBatch}
            className="inline-flex items-center gap-1.5 rounded-lg bg-[#00529C] px-3 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-[#003f7a] dark:bg-emerald-600 dark:hover:bg-emerald-500 cursor-pointer disabled:opacity-50"
          >
            <Zap className="h-3.5 w-3.5" />
            <span>
              {runningBatch ? 'Memproses Batch...' : 'Evaluasi Otomatis 5 Skenario'}
            </span>
          </button>
        </div>
      </div>

      {/* 4 Executive KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card 1: Total Klaim & Nilai Tagihan */}
        <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-900/60">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Total Antrean Klaim Aktif
            </span>
            <Database className="h-4 w-4 text-[#00529C] dark:text-sky-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white">
              {kpiStats.total}
            </span>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              berkas RITL (Sampel dari 195.544)
            </span>
          </div>
          <div className="mt-2 flex items-center justify-between border-t border-slate-200/70 pt-2 text-xs dark:border-slate-800">
            <span className="text-slate-500 dark:text-slate-400">Total Tagihan (FKL47):</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">
              {formatRupiah(kpiStats.totalBilled, true)}
            </span>
          </div>
        </div>

        {/* Card 2: Efisiensi Fast-Track */}
        <div className="rounded-xl border border-emerald-500/25 bg-emerald-50/40 p-4 dark:border-emerald-500/20 dark:bg-emerald-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
              Jalur Cepat (Fast-Track)
            </span>
            <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-emerald-700 dark:text-emerald-400">
              {kpiStats.fastTrackPct}%
            </span>
            <span className="text-xs font-medium text-emerald-700/80 dark:text-emerald-300/80">
              ({kpiStats.lowCount} Klaim Low Risk)
            </span>
          </div>
          <div className="mt-2 flex items-center justify-between border-t border-emerald-500/20 pt-2 text-xs">
            <span className="text-emerald-800/80 dark:text-emerald-300/80">
              Populasi Empiris RITL:
            </span>
            <span className="font-bold text-emerald-800 dark:text-emerald-300">
              94.34% Lolos Otomatis
            </span>
          </div>
        </div>

        {/* Card 3: Klaim Prioritas Audit Tinggi & Sedang */}
        <div className="rounded-xl border border-red-500/25 bg-red-50/40 p-4 dark:border-red-500/20 dark:bg-red-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-red-800 dark:text-red-300">
              Prioritas Audit (High & Med)
            </span>
            <ShieldAlert className="h-4 w-4 text-red-600 dark:text-red-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-3">
            <span className="text-2xl font-extrabold text-red-600 dark:text-red-400">
              {kpiStats.highCount} Merah
            </span>
            <span className="text-sm font-bold text-amber-600 dark:text-amber-400">
              • {kpiStats.medCount} Kuning
            </span>
          </div>
          <div className="mt-2 flex items-center justify-between border-t border-red-500/20 pt-2 text-xs">
            <span className="text-red-800/80 dark:text-red-300/80">
              Eksposur Tagihan High-Risk:
            </span>
            <span className="font-bold text-red-700 dark:text-red-300">
              {formatRupiah(kpiStats.highRiskBilled, true)}
            </span>
          </div>
        </div>

        {/* Card 4: Estimasi Penghematan Dana JKN / Pencegahan Dispute */}
        <div className="rounded-xl border border-[#00529C]/25 bg-gradient-to-br from-[#00529C]/5 to-emerald-500/10 p-4 dark:border-sky-500/30 dark:from-sky-950/40 dark:to-emerald-950/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#00529C] dark:text-sky-300">
              Estimasi Penyelamatan Dana JKN
            </span>
            <Wallet className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-xl font-extrabold text-[#00529C] dark:text-emerald-400 sm:text-2xl">
              {formatRupiah(kpiStats.potentialDisputeIdr, true)}
            </span>
          </div>
          <div className="mt-2 flex items-center justify-between border-t border-[#00529C]/15 pt-2 text-xs dark:border-sky-500/20">
            <span className="text-slate-600 dark:text-slate-300">
              Terkonfirmasi Audit Verifikator:
            </span>
            <span className="font-bold text-emerald-700 dark:text-emerald-300">
              {formatRupiah(kpiStats.confirmedAuditSavingsIdr, true)}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
