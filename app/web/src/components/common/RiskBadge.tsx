import React from 'react';
import type { RiskCategory } from '../../types/jagaKode';

interface RiskBadgeProps {
  category: RiskCategory;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ category }) => {
  if (category === 'HIGH_RISK') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/15 px-2.5 py-1 text-xs font-bold text-red-600 dark:bg-red-500/20 dark:text-red-400 border border-red-500/30">
        <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
        HIGH RISK
      </span>
    );
  }
  if (category === 'MEDIUM_RISK') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/15 px-2.5 py-1 text-xs font-bold text-amber-700 dark:bg-amber-500/20 dark:text-amber-300 border border-amber-500/30">
        <span className="h-2 w-2 rounded-full bg-amber-500" />
        MEDIUM RISK
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-bold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 border border-emerald-500/30">
      <span className="h-2 w-2 rounded-full bg-emerald-500" />
      FAST-TRACK
    </span>
  );
};
