import React from 'react';
import { Sparkles } from 'lucide-react';

export interface BannerInfo {
  type: 'success' | 'warning' | 'error' | 'info';
  text: string;
}

interface NotificationBannerProps {
  banner: BannerInfo | null;
  onClose: () => void;
}

export const NotificationBanner: React.FC<NotificationBannerProps> = ({
  banner,
  onClose,
}) => {
  if (!banner) return null;

  return (
    <div
      className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-2.5 text-xs font-medium shadow-2xs ${
        banner.type === 'success'
          ? 'border-emerald-500/40 bg-emerald-50 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-200'
          : banner.type === 'error'
          ? 'border-red-500/40 bg-red-50 text-red-900 dark:bg-red-950/50 dark:text-red-200'
          : banner.type === 'warning'
          ? 'border-amber-500/40 bg-amber-50 text-amber-900 dark:bg-amber-950/50 dark:text-amber-200'
          : 'border-sky-500/40 bg-sky-50 text-sky-900 dark:bg-sky-950/50 dark:text-sky-200'
      }`}
    >
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 shrink-0" />
        <span>{banner.text}</span>
      </div>
      <button
        type="button"
        onClick={onClose}
        className="text-xs font-bold underline opacity-75 hover:opacity-100 cursor-pointer"
      >
        Tutup
      </button>
    </div>
  );
};
