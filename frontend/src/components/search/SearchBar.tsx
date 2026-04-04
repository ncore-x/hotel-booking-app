import { useSearchStore } from "../../stores/searchStore";
import { getDefaultDateFrom } from "../../lib/dates";
import { useT } from "../../i18n/useT";

const today = getDefaultDateFrom();

export function SearchBar() {
  const { dateFrom, dateTo, location, title, setDates, setLocation, setTitle } =
    useSearchStore();
  const t = useT();

  return (
    <div className="w-full">
      {/* Search panel */}
      <div className="rounded-2xl bg-card shadow-lg">
        <div className="flex flex-col gap-0 divide-y divide-divider lg:flex-row lg:divide-x lg:divide-y-0">
          {/* Location */}
          <div className="flex flex-1 items-center gap-3 px-5 py-4">
            <svg className="h-5 w-5 flex-shrink-0 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
            </svg>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted">{t.search.location}</p>
              <input
                type="text"
                placeholder={t.search.locationPlaceholder}
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full border-none bg-transparent p-0 text-sm font-medium text-ink placeholder-subtle focus:outline-none"
              />
            </div>
          </div>

          {/* Name */}
          <div className="flex flex-1 items-center gap-3 px-5 py-4">
            <svg className="h-5 w-5 flex-shrink-0 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted">{t.search.hotelName}</p>
              <input
                type="text"
                placeholder={t.search.hotelNamePlaceholder}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full border-none bg-transparent p-0 text-sm font-medium text-ink placeholder-subtle focus:outline-none"
              />
            </div>
          </div>

          {/* Check-in */}
          <div className="flex flex-1 items-center gap-3 px-5 py-4">
            <svg className="h-5 w-5 flex-shrink-0 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
            </svg>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted">{t.search.checkIn}</p>
              <input
                type="date"
                value={dateFrom}
                min={today}
                onChange={(e) => setDates(e.target.value, dateTo)}
                className="w-full border-none bg-transparent p-0 text-sm font-medium text-ink focus:outline-none"
              />
            </div>
          </div>

          {/* Check-out */}
          <div className="flex flex-1 items-center gap-3 px-5 py-4">
            <svg className="h-5 w-5 flex-shrink-0 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
            </svg>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted">{t.search.checkOut}</p>
              <input
                type="date"
                value={dateTo}
                min={dateFrom}
                onChange={(e) => setDates(dateFrom, e.target.value)}
                className="w-full border-none bg-transparent p-0 text-sm font-medium text-ink focus:outline-none"
              />
            </div>
          </div>

          {/* Nights between dates */}
          {dateFrom && dateTo && new Date(dateTo) > new Date(dateFrom) && (
            <div className="flex flex-shrink-0 items-center gap-2 px-5 py-4 text-sm font-medium text-muted">
              <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {t.search.nights(Math.round((new Date(dateTo).getTime() - new Date(dateFrom).getTime()) / 86400000))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
