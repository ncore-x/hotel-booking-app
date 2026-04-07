import { useState, useRef, useEffect } from "react";
import { useT } from "../../i18n/useT";

interface GuestSelectorProps {
  guests: number;
  onChange: (guests: number) => void;
}

export function GuestSelector({ guests, onChange }: GuestSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const t = useT();

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={ref} className="relative min-w-0 flex-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-5 py-4 text-left"
      >
        <svg
          className="h-5 w-5 flex-shrink-0 text-muted"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
          />
        </svg>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted">{t.search.guests}</p>
          <p className="text-sm font-medium text-ink">{t.search.guestsLabel(guests)}</p>
        </div>
        <svg
          className={`h-4 w-4 flex-shrink-0 text-muted transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      {open && (
        <div className="absolute left-0 top-full z-50 w-64 rounded-2xl border border-divider bg-card p-4 shadow-xl">
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-medium text-ink">{t.search.adults}</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => onChange(Math.max(1, guests - 1))}
                disabled={guests <= 1}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-divider text-ink transition-colors hover:border-ink disabled:cursor-not-allowed disabled:opacity-30"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 12h-15" />
                </svg>
              </button>
              <span className="w-6 text-center text-sm font-semibold text-ink">{guests}</span>
              <button
                type="button"
                onClick={() => onChange(Math.min(10, guests + 1))}
                disabled={guests >= 10}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-divider text-ink transition-colors hover:border-ink disabled:cursor-not-allowed disabled:opacity-30"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setOpen(false)}
            className="mt-3 w-full rounded-xl bg-brand py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv"
          >
            {t.search.done}
          </button>
        </div>
      )}
    </div>
  );
}
