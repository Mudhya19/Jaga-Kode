import React from 'react';
import { BarChart3 } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type {
  ClaimEvaluationResponse,
  PeerGroupStatsResponse,
} from '../../types/jagaKode';
import { estimateClaimDisputeIdr } from '../../constants/presetScenarios';
import { formatRupiah } from '../../utils/formatters';

interface CostComparisonCardProps {
  claim: ClaimEvaluationResponse;
  peerStats: PeerGroupStatsResponse | null;
  isDark: boolean;
}

export const CostComparisonCard: React.FC<CostComparisonCardProps> = ({
  claim,
  peerStats,
  isDark,
}) => {
  const peerMedianCost =
    peerStats?.profile?.median_cost && peerStats.profile.median_cost > 0
      ? peerStats.profile.median_cost
      : 3680400;

  const costComparisonData = [
    {
      name: 'Tagihan RS (FKL47)',
      nominal: claim.FKL47 ?? 0,
      color: claim.badge_color,
    },
    {
      name: 'Acuan INA-CBG (FKL32)',
      nominal:
        claim.FKL32 && claim.FKL32 > 0 ? claim.FKL32 : claim.FKL47,
      color: '#00529C',
    },
    {
      name: 'Median Biaya Peer',
      nominal: peerMedianCost,
      color: '#10b981',
    },
  ];

  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3.5 dark:border-slate-800 dark:bg-slate-900/50">
      <div className="mb-2 flex items-center justify-between">
        <div>
          <h3 className="text-xs font-bold text-slate-900 dark:text-white">
            Perbandingan Tagihan RS (FKL47) vs Standar INA-CBG (FKL32)
          </h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            Referensi Peer Group:{' '}
            <span className="font-mono font-semibold">
              {peerStats?.peer_group_id || claim.peer_group_id || 'Global'}
            </span>{' '}
            (
            {peerStats?.resolution_level
              ? peerStats.resolution_level.replace(/_/g, ' ')
              : 'Kelompok Sebaya'}
            )
          </p>
        </div>
        <BarChart3 className="h-4 w-4 text-[#00529C] dark:text-sky-400" />
      </div>

      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={costComparisonData}
            layout="vertical"
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={isDark ? '#1e293b' : '#e2e8f0'}
            />
            <XAxis
              type="number"
              tickFormatter={(v) => `${(Number(v) / 1_000_000).toFixed(1)}Jt`}
              tick={{ fill: isDark ? '#94a3b8' : '#475569', fontSize: 10 }}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={125}
              tick={{
                fill: isDark ? '#e2e8f0' : '#1e293b',
                fontSize: 10,
                fontWeight: 600,
              }}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const val = payload[0].value as number;
                  return (
                    <div className="rounded-xl border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur-xs dark:border-slate-700 dark:bg-slate-900/95">
                      <p className="text-xs font-bold text-[#00529C] dark:text-sky-400">
                        {label}
                      </p>
                      <p className="mt-1 font-mono text-xs font-semibold text-slate-800 dark:text-slate-200">
                        Nominal:{' '}
                        <span className="font-extrabold text-emerald-600 dark:text-emerald-400">
                          {formatRupiah(val)}
                        </span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="nominal" radius={[0, 6, 6, 0]}>
              {costComparisonData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Peer Group Statistical Telemetry Cards */}
      <div className="mt-2 grid grid-cols-3 gap-2 border-t border-slate-200/80 pt-2.5 text-center dark:border-slate-800">
        <div className="rounded-lg bg-white p-2 dark:bg-slate-800/90">
          <div className="text-[10px] text-slate-500 dark:text-slate-400">
            Rasio Biaya Peer
          </div>
          <div className="font-mono text-xs font-extrabold text-slate-900 dark:text-white">
            {claim.cost_peer_ratio.toFixed(2)}x
          </div>
        </div>
        <div className="rounded-lg bg-white p-2 dark:bg-slate-800/90">
          <div className="text-[10px] text-slate-500 dark:text-slate-400">
            LoS Klaim vs Peer
          </div>
          <div className="font-mono text-xs font-extrabold text-slate-900 dark:text-white">
            {claim.los ?? 0} hr vs{' '}
            {(peerStats?.profile?.mean_los ?? 3.4).toFixed(1)} hr
          </div>
        </div>
        <div className="rounded-lg bg-white p-2 dark:bg-slate-800/90">
          <div className="text-[10px] text-slate-500 dark:text-slate-400">
            Z-Score LoS Peer
          </div>
          <div className="font-mono text-xs font-extrabold text-slate-900 dark:text-white">
            {claim.los_peer_zscore >= 0 ? '+' : ''}
            {claim.los_peer_zscore.toFixed(2)} SD
          </div>
        </div>
      </div>

      {/* Secondary Diagnoses Box */}
      <div className="mt-3 rounded-xl border border-slate-200/80 bg-white p-3 dark:border-slate-800 dark:bg-slate-900/60">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
            Diagnosis Sekunder (FKL24) & Atribut Klinis:
          </span>
          <span className="rounded bg-slate-200 px-1.5 py-0.5 font-mono text-[10px] font-bold dark:bg-slate-800">
            {claim.comorbidity_count} Komorbiditas
          </span>
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {claim.secondary_diagnoses &&
          claim.secondary_diagnoses.length > 0 ? (
            claim.secondary_diagnoses.map((code) => (
              <span
                key={code}
                className="rounded-md border border-slate-300 bg-white px-2 py-0.5 font-mono text-xs font-bold text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                ICD-10: {code}
              </span>
            ))
          ) : (
            <span className="text-xs italic text-slate-400">
              Tidak ada diagnosis sekunder yang diklaimkan
            </span>
          )}
        </div>
        <div className="mt-2.5 flex flex-wrap gap-3 text-[11px] text-slate-500 dark:text-slate-400">
          <span>
            Komorbiditas Mayor (MCC):{' '}
            <strong className="text-slate-800 dark:text-slate-200">
              {claim.has_severe_comorbidity ? 'YA (Terdeteksi)' : 'TIDAK'}
            </strong>
          </span>
          <span>•</span>
          <span>
            Estimasi Selisih Dispute:{' '}
            <strong className="text-red-600 dark:text-red-400">
              {formatRupiah(estimateClaimDisputeIdr(claim))}
            </strong>
          </span>
        </div>
      </div>
    </div>
  );
};
