import React from 'react';
import type {
  ClaimEvaluationResponse,
  PeerGroupStatsResponse,
  VerifierDecision,
} from '../../types/jagaKode';
import { ClaimInspectorHeader } from './ClaimInspectorHeader';
import { ClinicalRulesCard } from './ClinicalRulesCard';
import { CostComparisonCard } from './CostComparisonCard';
import { XaiRadarCard } from './XaiRadarCard';

interface ClaimDetailInspectorProps {
  claim: ClaimEvaluationResponse;
  auditDecision?: VerifierDecision;
  peerStats: PeerGroupStatsResponse | null;
  isDark: boolean;
}

export const ClaimDetailInspector: React.FC<ClaimDetailInspectorProps> = ({
  claim,
  auditDecision,
  peerStats,
  isDark,
}) => {
  return (
    <section
      aria-label="Claim Detail Inspector & 5-Axis Explainability Radar"
      className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-[#111827] sm:p-5"
    >
      {/* Inspector Header & Dual Fusion Score */}
      <ClaimInspectorHeader claim={claim} auditDecision={auditDecision} />

      {/* 2-Column Visual XAI Grid: 5-Axis Radar Chart + Financial & Peer Comparison */}
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <XaiRadarCard claim={claim} isDark={isDark} />
        <CostComparisonCard claim={claim} peerStats={peerStats} isDark={isDark} />
      </div>

      {/* 5 Permenkes No. 26/2021 Clinical Consistency Rules Breakdown */}
      <ClinicalRulesCard claim={claim} />
    </section>
  );
};
