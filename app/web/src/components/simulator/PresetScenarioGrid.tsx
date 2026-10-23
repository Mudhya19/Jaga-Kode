import React from 'react';
import { Play } from 'lucide-react';
import { PRESET_SCENARIOS } from '../../constants/presetScenarios';
import type { PresetCaseKey } from '../../types/jagaKode';
import { formatRiskLabel } from '../../utils/formatters';

interface PresetScenarioGridProps {
  activePresetKey: PresetCaseKey | null;
  evaluatingClaim: boolean;
  onSelectPreset: (key: PresetCaseKey) => void;
}

export const PresetScenarioGrid: React.FC<PresetScenarioGridProps> = ({
  activePresetKey,
  evaluatingClaim,
  onSelectPreset,
}) => {
  return (
    <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {PRESET_SCENARIOS.map((scn) => {
        const isSelected = activePresetKey === scn.key;
        const isNormal = scn.expectedTier === 'LOW_RISK';
        return (
          <button
            key={scn.key}
            type="button"
            disabled={evaluatingClaim}
            onClick={() => onSelectPreset(scn.key)}
            className={`group flex flex-col justify-between rounded-xl border p-3.5 text-left transition-all cursor-pointer ${
              isSelected
                ? 'border-emerald-500 bg-emerald-50/70 ring-2 ring-emerald-500/30 dark:border-emerald-400 dark:bg-emerald-950/40'
                : 'border-slate-200 bg-slate-50/60 hover:border-emerald-500/50 hover:bg-white dark:border-slate-800 dark:bg-slate-900/60 dark:hover:border-emerald-500/50 dark:hover:bg-slate-900'
            }`}
          >
            <div>
              <div className="flex items-center justify-between gap-2">
                <span
                  className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-extrabold uppercase ${
                    isNormal
                      ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                      : 'bg-red-500/15 text-red-600 dark:text-red-400'
                  }`}
                >
                  {formatRiskLabel(scn.badge)}
                </span>
                <Play className="h-3.5 w-3.5 text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400" />
              </div>
              <h3 className="mt-2 text-xs font-bold text-slate-900 dark:text-white">
                {scn.title}
              </h3>
              <p className="mt-0.5 font-mono text-[11px] font-semibold text-[#00529C] dark:text-sky-400">
                {scn.subtitle}
              </p>
              <p className="mt-1.5 text-[11px] leading-relaxed text-slate-500 dark:text-slate-400">
                {scn.description}
              </p>
            </div>
            <div className="mt-3 flex items-center justify-between border-t border-slate-200/70 pt-2 text-[11px] font-semibold text-emerald-700 dark:border-slate-800 dark:text-emerald-400">
              <span>Uji Skenario 1-Klik</span>
              <span>→</span>
            </div>
          </button>
        );
      })}
    </div>
  );
};
