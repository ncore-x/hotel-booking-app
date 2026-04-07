import { useState, useEffect, useRef } from "react";
import { format } from "date-fns";
import type { Locale } from "date-fns";
import { ru, enUS } from "date-fns/locale";
import { useSearchStore } from "../../stores/searchStore";
import { hotelsApi } from "../../api/hotels";
import { useDebounce } from "../../hooks/useDebounce";
import { useT } from "../../i18n/useT";
import { useLangStore } from "../../stores/langStore";
import { DateRangePicker } from "./DateRangePicker";
import { GuestSelector } from "./GuestSelector";
import type { AutocompleteResult } from "../../types/hotel";

function formatDisplayDay(dateStr: string, locale: Locale): string {
  return format(new Date(dateStr + "T12:00:00"), "d MMM", { locale });
}

export function SearchBar() {
  const { dateFrom, dateTo, setDates, setCity, setTitle, setSearch, setGuests } = useSearchStore();
  const storeCity = useSearchStore((s) => s.city);
  const storeTitle = useSearchStore((s) => s.title);
  const storeGuests = useSearchStore((s) => s.guests);
  const [pendingGuests, setPendingGuests] = useState(storeGuests);
  const [pendingDateFrom, setPendingDateFrom] = useState(dateFrom);
  const [pendingDateTo, setPendingDateTo] = useState(dateTo);
  const t = useT();
  const { lang } = useLangStore();
  const locale = lang === "ru" ? ru : enUS;

  // ─── Destination field ─────────────────────────────────────────────────
  const [query, setQuery] = useState(storeCity || storeTitle);
  const [pendingCity, setPendingCity] = useState(storeCity);
  const [pendingTitle, setPendingTitle] = useState(storeTitle);
  const [suggestions, setSuggestions] = useState<AutocompleteResult>({ locations: [], hotels: [] });
  const [popularLocations, setPopularLocations] = useState<string[]>([]);
  const [suggestOpen, setSuggestOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const debouncedQuery = useDebounce(query, 300);
  const destinationRef = useRef<HTMLDivElement>(null);

  // Load popular cities once on mount
  useEffect(() => {
    hotelsApi.popularLocations().then(setPopularLocations).catch(() => {});
  }, []);

  useEffect(() => {
    if (!debouncedQuery.trim() || debouncedQuery.length < 2) {
      setSuggestions({ locations: [], hotels: [] });
      return;
    }
    let cancelled = false;
    hotelsApi.autocomplete(debouncedQuery).then((res) => {
      if (!cancelled) {
        setSuggestions(res);
        setActiveIdx(-1);
      }
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [debouncedQuery]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (destinationRef.current && !destinationRef.current.contains(e.target as Node)) {
        setSuggestOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const isQueryEmpty = !query.trim() || query.length < 2;

  const displayLocations = isQueryEmpty ? popularLocations : suggestions.locations;
  const displayHotels = isQueryEmpty ? [] : suggestions.hotels;

  const allSuggestions: Array<{ type: "location" | "hotel"; label: string; sublabel?: string }> = [
    ...displayLocations.map((loc) => ({ type: "location" as const, label: loc })),
    ...displayHotels.map((h) => ({ type: "hotel" as const, label: h.title, sublabel: h.city })),
  ];

  function handleSelectCity(city: string) {
    setQuery(city);
    setPendingCity(city);
    setPendingTitle("");
    setSuggestOpen(false);
  }

  function handleSelectHotel(title: string) {
    setQuery(title);
    setPendingCity("");
    setPendingTitle(title);
    setSuggestOpen(false);
  }

  function handleDestinationKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, allSuggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, -1));
    } else if (e.key === "Enter") {
      if (activeIdx >= 0 && allSuggestions[activeIdx]) {
        const s = allSuggestions[activeIdx];
        if (s.type === "location") handleSelectCity(s.label);
        else handleSelectHotel(s.label);
      } else {
        handleSearch();
      }
    } else if (e.key === "Escape") {
      setSuggestOpen(false);
    }
  }

  // ─── Date panel ────────────────────────────────────────────────────────
  const [dateOpen, setDateOpen] = useState(false);
  const dateRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (dateRef.current && !dateRef.current.contains(e.target as Node)) {
        setDateOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // ─── Search ─────────────────────────────────────────────────────────────
  function handleSearch() {
    const raw = query.trim();
    if (pendingCity) {
      // User picked a city suggestion
      setCity(pendingCity);
      setTitle("");
      setSearch("");
    } else if (pendingTitle) {
      // User picked a hotel suggestion
      setCity("");
      setTitle(pendingTitle);
      setSearch("");
    } else if (raw) {
      // User typed manually — broad search across city + title + address
      setCity("");
      setTitle("");
      setSearch(raw);
    } else {
      setCity("");
      setTitle("");
      setSearch("");
    }
    setGuests(pendingGuests);
    setDates(pendingDateFrom, pendingDateTo);
    setSuggestOpen(false);
    setDateOpen(false);
  }

  const nights = Math.round(
    (new Date(pendingDateTo).getTime() - new Date(pendingDateFrom).getTime()) / 86400000,
  );

  return (
    <div className="w-full">
      <div className="overflow-visible rounded-2xl bg-card shadow-lg">
        <div className="flex flex-col divide-y divide-divider lg:flex-row lg:divide-x lg:divide-y-0">

          {/* ── Destination ── */}
          <div ref={destinationRef} className="relative min-w-0 flex-[2]">
            <div className="flex items-center gap-3 px-5 py-4">
              <svg className="h-5 w-5 flex-shrink-0 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
              </svg>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted">{t.search.destination}</p>
                <input
                  type="text"
                  placeholder={t.search.destinationPlaceholder}
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setPendingCity("");
                    setPendingTitle("");
                  }}
                  onKeyDown={handleDestinationKeyDown}
                  onFocus={() => setSuggestOpen(true)}
                  autoComplete="off"
                  className="w-full border-none bg-transparent p-0 text-sm font-medium text-ink placeholder-subtle focus:outline-none"
                />
              </div>
            </div>

            {/* Autocomplete dropdown */}
            {suggestOpen && allSuggestions.length > 0 && (
              <ul className="absolute left-0 top-full z-50 w-full min-w-[280px] overflow-hidden rounded-xl border border-divider bg-card shadow-lg">
                {displayLocations.length > 0 && (
                  <>
                    <li className="px-4 pb-1 pt-3">
                      <span className="text-[10px] font-bold uppercase tracking-widest text-subtle">
                        {isQueryEmpty
                          ? (lang === "ru" ? "Популярные направления" : "Popular destinations")
                          : (lang === "ru" ? "Города" : "Cities")}
                      </span>
                    </li>
                    {displayLocations.map((loc, i) => (
                      <li key={`loc-${loc}`}>
                        <button
                          type="button"
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => handleSelectCity(loc)}
                          className={`flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                            i === activeIdx ? "bg-secondary text-ink" : "text-muted hover:bg-secondary hover:text-ink"
                          }`}
                        >
                          <svg className="h-3.5 w-3.5 shrink-0 text-subtle" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                          </svg>
                          {loc}
                        </button>
                      </li>
                    ))}
                  </>
                )}

                {displayHotels.length > 0 && (
                  <>
                    <li className="px-4 pb-1 pt-3">
                      <span className="text-[10px] font-bold uppercase tracking-widest text-subtle">{t.search.sections.hotels}</span>
                    </li>
                    {displayHotels.map((hotel, i) => {
                      const idx = displayLocations.length + i;
                      return (
                        <li key={`hotel-${hotel.title}`}>
                          <button
                            type="button"
                            onMouseDown={(e) => e.preventDefault()}
                            onClick={() => handleSelectHotel(hotel.title)}
                            title={[hotel.title, hotel.city, hotel.address].filter(Boolean).join(", ")}
                            className={`flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                              idx === activeIdx ? "bg-secondary" : "hover:bg-secondary"
                            }`}
                          >
                            <svg className="h-3.5 w-3.5 shrink-0 text-subtle" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
                            </svg>
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium text-ink">{hotel.title}</p>
                              <p className="truncate text-xs text-muted">
                                {hotel.city}{hotel.address ? `, ${hotel.address}` : ""}
                              </p>
                            </div>
                          </button>
                        </li>
                      );
                    })}
                  </>
                )}
              </ul>
            )}
          </div>

          {/* ── Dates ── */}
          <div ref={dateRef} className="relative flex-[2]">
            <button
              type="button"
              onClick={() => setDateOpen((v) => !v)}
              className="flex w-full items-center gap-3 px-5 py-4 text-left"
            >
              <svg className="h-5 w-5 flex-shrink-0 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
              </svg>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                  {t.search.checkIn} — {t.search.checkOut}
                </p>
                <p className="text-sm font-medium text-ink">
                  {formatDisplayDay(pendingDateFrom, locale)}
                  <span className="mx-1.5 text-muted">—</span>
                  {formatDisplayDay(pendingDateTo, locale)}
                  {nights > 0 && (
                    <span className="ml-2 text-xs font-normal text-muted">· {t.search.nights(nights)}</span>
                  )}
                </p>
              </div>
              <svg
                className={`h-4 w-4 flex-shrink-0 text-muted transition-transform ${dateOpen ? "rotate-180" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>

            {dateOpen && (
              <div className="absolute left-0 top-full z-50 mt-1 w-max">
                <DateRangePicker
                  dateFrom={pendingDateFrom}
                  dateTo={pendingDateTo}
                  onChange={(from, to) => {
                    setPendingDateFrom(from);
                    setPendingDateTo(to);
                  }}
                  onClose={() => setDateOpen(false)}
                />
              </div>
            )}
          </div>

          {/* ── Guests ── */}
          <GuestSelector guests={pendingGuests} onChange={setPendingGuests} />

          {/* ── Search button ── */}
          <div className="flex items-center px-4 py-3 lg:py-0">
            <button
              onClick={handleSearch}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv lg:w-auto"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              {t.search.searchButton}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
