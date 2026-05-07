'use client';

import Link from 'next/link';
import type { WatchlistAsset } from './ChartComponent';

interface WatchlistProps {
  assets: WatchlistAsset[];
  prices: Record<WatchlistAsset, number | null>;
  selectedAsset: WatchlistAsset;
  onSelectAsset: (asset: WatchlistAsset) => void;
  subscriptionActive: boolean;
}

function formatPrice(price: number | null): string {
  if (price === null) {
    return '--';
  }

  return price.toLocaleString(undefined, {
    minimumFractionDigits: price < 1 ? 4 : 2,
    maximumFractionDigits: price < 1 ? 4 : 2,
  });
}

export default function Watchlist({
  assets,
  prices,
  selectedAsset,
  onSelectAsset,
  subscriptionActive,
}: WatchlistProps) {
  return (
    <div className="flex h-full flex-col">
      {/* Premium Message Banner */}
      {subscriptionActive && (
        <div className="mb-4 rounded-xl border border-cyan-500/30 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/20">
              <svg className="h-5 w-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-sm font-bold text-cyan-400">Premium Unlocked!</p>
              <p className="text-xs text-slate-400 mt-0.5">
                Select asset to view full analytics
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-400">Watchlist</p>
        <h2 className="mt-1 text-xl font-bold text-white">Premium Assets</h2>
        <p className="mt-2 text-base font-semibold text-slate-300">
          Click any asset to view live chart
        </p>
      </div>

      <div className="space-y-3">
        {assets.map((asset) => {
          const isSelected = asset === selectedAsset;
          const price = prices[asset];

          return (
            <button
              key={asset}
              type="button"
              onClick={() => onSelectAsset(asset)}
              className={`w-full rounded-xl border px-4 py-4 text-left transition ${
                isSelected
                  ? 'border-cyan-500/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/20'
                  : 'border-slate-800/50 bg-[#0f1419] hover:border-slate-700/50'
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-white">{asset}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">Live Market Feed</p>
                </div>

                <div className="text-right">
                  <p className="text-sm font-semibold text-slate-100">${formatPrice(price)}</p>
                  <p className={`mt-1 text-xs ${isSelected ? 'text-cyan-300' : 'text-slate-500'}`}>
                    {isSelected ? '● Active' : 'Select'}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
        <p className="text-sm font-medium text-white">Signal Marker Guide</p>
        <div className="mt-3 space-y-2 text-sm text-slate-400">
          <div className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#26a69a]" />
            <span>BUY: green up arrow below candle</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#ef5350]" />
            <span>SELL: red down arrow above candle</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#fdd835]" />
            <span>HOLD: yellow circle marker</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#fb8c00]" />
            <span>STOP LOSS: orange exit marker</span>
          </div>
        </div>
      </div>
    </div>
  );
}