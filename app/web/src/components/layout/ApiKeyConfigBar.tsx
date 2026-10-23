import React from 'react';
import { Lock } from 'lucide-react';

interface ApiKeyConfigBarProps {
  show: boolean;
  apiKey: string;
  setApiKey: (key: string) => void;
  onApply: () => void;
}

export const ApiKeyConfigBar: React.FC<ApiKeyConfigBarProps> = ({
  show,
  apiKey,
  setApiKey,
  onApply,
}) => {
  if (!show) return null;

  return (
    <div className="border-b border-slate-200 bg-slate-50 px-4 py-2 dark:border-slate-800 dark:bg-slate-900/90">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
          <Lock className="h-3.5 w-3.5 text-emerald-600" />
          <span>
            Header Keamanan <code className="font-mono font-bold">X-API-Key</code> (kosongkan
            jika variabel lingkungan <code className="font-mono">JAGA_KODE_API_KEY</code> tidak
            diaktifkan di server):
          </span>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Masukkan X-API-Key opsional..."
            className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
          />
          <button
            type="button"
            onClick={onApply}
            className="rounded-md bg-emerald-600 px-3 py-1 font-semibold text-white hover:bg-emerald-700 cursor-pointer"
          >
            Terapkan
          </button>
        </div>
      </div>
    </div>
  );
};
