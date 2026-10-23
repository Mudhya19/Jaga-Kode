import React from 'react';
import { Activity } from 'lucide-react';
import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { ClaimEvaluationResponse } from '../../types/jagaKode';
import { formatNarrativeText } from '../../utils/formatters';

interface XaiRadarCardProps {
  claim: ClaimEvaluationResponse;
  isDark: boolean;
}

export const XaiRadarCard: React.FC<XaiRadarCardProps> = ({ claim, isDark }) => {
  const radarChartData = [
    {
      axis: 'Deviasi LoS',
      score: claim.radar.los_deviation,
      baseline: 30,
      metric: 'Lama Rawat Inap (LoS)',
    },
    {
      axis: 'Deviasi Biaya',
      score: claim.radar.cost_deviation,
      baseline: 35,
      metric: 'Rasio Biaya vs Peer Median',
    },
    {
      axis: 'Komorbiditas',
      score: claim.radar.comorbidity_intensity,
      baseline: 25,
      metric: 'Intensitas Diagnosis Sekunder',
    },
    {
      axis: 'Severity Lvl',
      score: claim.radar.severity_level,
      baseline: 30,
      metric: 'Eskalasi Tingkat Keparahan',
    },
    {
      axis: 'Kepatuhan Reg.',
      score: claim.radar.regulatory_violation,
      baseline: 20,
      metric: 'Pelanggaran Permenkes 26/2021',
    },
  ];

  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3.5 dark:border-slate-800 dark:bg-slate-900/50">
      <div className="mb-2 flex items-center justify-between">
        <div>
          <h3 className="text-xs font-bold text-slate-900 dark:text-white">
            5-Axis Explainability Radar (XAI)
          </h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            Profil Risiko Klaim vs Ambang Normal Peer Group
          </p>
        </div>
        <Activity className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="72%" data={radarChartData}>
            <PolarGrid
              stroke={isDark ? '#334155' : '#cbd5e1'}
              strokeDasharray="3 3"
            />
            <PolarAngleAxis
              dataKey="axis"
              tick={{
                fill: isDark ? '#e2e8f0' : '#1e293b',
                fontSize: 11,
                fontWeight: 600,
              }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: isDark ? '#94a3b8' : '#64748b', fontSize: 10 }}
            />
            <Radar
              name="Ambang Normal Peer"
              dataKey="baseline"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.18}
            />
            <Radar
              name="Skor Klaim Ini"
              dataKey="score"
              stroke={claim.badge_color}
              fill={claim.badge_color}
              fillOpacity={0.45}
            />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const p = payload[0];
                  return (
                    <div className="rounded-xl border border-slate-200 bg-white/95 p-2.5 shadow-lg backdrop-blur-xs dark:border-slate-700 dark:bg-slate-900/95">
                      <p className="text-xs font-bold text-[#00529C] dark:text-sky-400">
                        {p.name || (p.payload as any)?.metric || 'Metrik XAI'}
                      </p>
                      <p className="mt-1 font-mono text-xs font-extrabold text-slate-800 dark:text-slate-100">
                        Skor: {p.value} / 100
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Clinical Narrative List */}
      <div className="mt-3 rounded-xl border border-slate-200/80 bg-white p-3 dark:border-slate-800 dark:bg-slate-900/60">
        <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
          Bukti Narasi Klinis XAI (Clinical Narrative):
        </div>
        <ul className="mt-1.5 space-y-1 text-xs text-slate-600 dark:text-slate-300">
          {claim.clinical_narrative.map((line, i) => (
            <li key={i} className="flex items-start gap-1.5">
              <span className="font-bold text-emerald-600 dark:text-emerald-400">
                •
              </span>
              <span>{formatNarrativeText(line)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
