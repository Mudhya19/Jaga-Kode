import React from 'react';
import { AlertOctagon, CheckCircle2 } from 'lucide-react';
import { PERMENKES_RULES_CATALOG } from '../../constants/clinicalRules';
import type { ClaimEvaluationResponse } from '../../types/jagaKode';

interface ClinicalRulesCardProps {
  claim: ClaimEvaluationResponse;
}

export const ClinicalRulesCard: React.FC<ClinicalRulesCardProps> = ({ claim }) => {
  return (
    <div className="mt-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
          Kartu Pemeriksaan 5 Aturan Klinis Deterministik (Permenkes No. 26/2021 & No. 16/2019)
        </h3>
        <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
          {claim.rule_violations.length} dari 5 aturan terpicu
        </span>
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {PERMENKES_RULES_CATALOG.map((rule) => {
          const violated = claim.rule_violations.includes(rule.code);
          return (
            <div
              key={rule.code}
              className={`rounded-xl border p-3 transition-colors ${
                violated
                  ? 'border-red-500/40 bg-red-50/70 dark:border-red-500/40 dark:bg-red-950/30'
                  : 'border-slate-200/80 bg-white dark:border-slate-800 dark:bg-slate-900/40'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  {violated ? (
                    <AlertOctagon className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  )}
                  <span className="font-mono text-xs font-bold text-slate-900 dark:text-white">
                    {rule.title}
                  </span>
                </div>
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 font-mono text-[10px] font-extrabold ${
                    violated
                      ? 'bg-red-600 text-white'
                      : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                  }`}
                >
                  {violated ? `TERPICU (+${rule.weight})` : 'PATUH'}
                </span>
              </div>
              <p className="mt-1 text-[11px] font-medium text-[#00529C] dark:text-sky-400">
                {rule.regulation}
              </p>
              <p className="mt-1 text-[11px] leading-relaxed text-slate-600 dark:text-slate-400">
                {rule.summary}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
