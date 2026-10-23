import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-8 border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500 dark:border-slate-800 dark:bg-[#0f172a] dark:text-slate-400">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-2 px-4 sm:px-6">
        <span>
          <strong>JAGA-KODE v2.0</strong> — AI Guardrail untuk Efisiensi Klaim JKN • Tim{' '}
          <strong>SI DANDANG</strong>
        </span>
        <span>
          Kepatuhan: Permenkes No. 26/2021 • Permenkes No. 16/2019 • UU PDP No. 27/2022 (Zero-PII)
        </span>
      </div>
    </footer>
  );
};
