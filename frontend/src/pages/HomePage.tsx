import { useState, useEffect, useRef, useMemo } from "react";
import { Link } from "react-router";
import { motion } from "framer-motion";
import { SearchBar } from "../components/search/SearchBar";
import { SortControls } from "../components/search/SortControls";
import { HotelGrid } from "../components/hotel/HotelGrid";
import { HotelCard } from "../components/hotel/HotelCard";
import { Pagination } from "../components/Pagination";
import { Spinner } from "../components/ui/Spinner";
import { useSearchStore } from "../stores/searchStore";
import { hotelsApi } from "../api/hotels";
import { useT } from "../i18n/useT";
import type { Hotel } from "../types/hotel";

const HERO_IMAGE =
  "https://images.unsplash.com/photo-1767950470198-c9cd97f8ed87?w=1800&q=85&auto=format&fit=crop";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

export function HomePage() {
  const tr = useT();
  const { dateFrom, dateTo, city, title, search, guests, sortBy, order, page, perPage, setPage, setCity } =
    useSearchStore();

  const [result, setResult] = useState<{
    items: Hotel[];
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  }>({ items: [], pages: 1, has_next: false, has_prev: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [allLocations, setAllLocations] = useState<string[]>([]);

  const trendingRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!dateFrom || !dateTo || dateTo <= dateFrom) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    hotelsApi
      .search({
        date_from: dateFrom,
        date_to: dateTo,
        city: city || undefined,
        title: title || undefined,
        search: search || undefined,
        guests,
        sort_by: sortBy,
        order,
        page,
        per_page: perPage,
      })
      .then((res) => {
        if (cancelled) return;
        setResult({
          items: res.items,
          pages: res.pages,
          has_next: res.has_next,
          has_prev: res.has_prev,
        });
      })
      .catch(() => {
        if (!cancelled) setError(tr.common.error);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [dateFrom, dateTo, city, title, search, guests, sortBy, order, page, perPage]);

  const scrollTrending = (dir: "left" | "right") => {
    if (!trendingRef.current) return;
    trendingRef.current.scrollBy({ left: dir === "left" ? -340 : 340, behavior: "smooth" });
  };

  const hasSearch = !!(city || title || search);

  const uniqueLocations = useMemo(() => {
    const seen = new Set<string>();
    const locs: string[] = [];
    for (const hotel of result.items) {
      if (hotel.city && !seen.has(hotel.city)) {
        seen.add(hotel.city);
        locs.push(hotel.city);
      }
    }
    return locs;
  }, [result.items]);

  return (
    <div className="bg-surface">
      {/* ── HERO ── */}
      <section className="relative flex h-[580px] items-center justify-center overflow-hidden">
        <img
          src={HERO_IMAGE}
          alt="Luxury hotel"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-black/40" />

        <div className="relative z-10 w-full text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-5xl font-black uppercase leading-none tracking-tight text-white md:text-7xl"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {tr.home.heroTitle.split("\n").map((line, i) => (
              <span key={i}>{line}{i === 0 && <br />}</span>
            ))}
          </motion.h1>
        </div>
      </section>

      {/* ── SEARCH BAR ── */}
      <div className="mx-auto max-w-5xl px-4 py-8 lg:px-8">
        <SearchBar />
      </div>

      {/* ── SEARCH RESULTS (shown when user is searching) ── */}
      {hasSearch && (
        <section className="mx-auto max-w-7xl px-4 py-10 lg:px-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold text-ink">
              {tr.home.trendingTitle}
            </h2>
            <SortControls />
          </div>
          {loading ? (
            <div className="flex justify-center py-16">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600 dark:border-red-900 dark:bg-red-900/20 dark:text-red-400">{error}</div>
          ) : (
            <>
              <HotelGrid hotels={result.items} />
              <div className="mt-6">
                <Pagination
                  page={page}
                  pages={result.pages}
                  hasNext={result.has_next}
                  hasPrev={result.has_prev}
                  onPageChange={setPage}
                />
              </div>
            </>
          )}
        </section>
      )}

      {!hasSearch && (
        <>
          {/* ── EXPLORE BY LOCATION ── */}
          {!loading && uniqueLocations.length > 0 && (
            <motion.section
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="mx-auto max-w-7xl px-4 pb-4 pt-2 lg:px-8"
            >
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
                {tr.home.exploreLocations}
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setCity("")}
                  className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                    city === ""
                      ? "bg-brand text-on-brand"
                      : "border border-divider text-muted hover:border-ink hover:text-ink"
                  }`}
                >
                  {tr.home.allLocations}
                </button>
                {uniqueLocations.map((loc) => (
                  <button
                    key={loc}
                    onClick={() => setCity(loc)}
                    className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                      city === loc
                        ? "bg-brand text-on-brand"
                        : "border border-divider text-muted hover:border-ink hover:text-ink"
                    }`}
                  >
                    {loc}
                  </button>
                ))}
              </div>
            </motion.section>
          )}

          {/* ── TOP TRENDING HOTELS ── */}
          <motion.section
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="py-16"
          >
            <div className="mx-auto max-w-7xl px-4 lg:px-8">
              <div className="mb-8 flex items-center justify-between">
                <h2
                  className="text-3xl font-black uppercase tracking-tight text-ink"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  {tr.home.trendingTitle}
                </h2>
                <div className="flex items-center gap-4">
                  <div className="flex gap-2">
                    <button
                      aria-label="Scroll left"
                      onClick={() => scrollTrending("left")}
                      className="flex h-9 w-9 items-center justify-center rounded-full border border-divider text-muted transition-colors hover:border-ink hover:text-ink"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
                      </svg>
                    </button>
                    <button
                      aria-label="Scroll right"
                      onClick={() => scrollTrending("right")}
                      className="flex h-9 w-9 items-center justify-center rounded-full border border-divider text-muted transition-colors hover:border-ink hover:text-ink"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="flex justify-center py-12">
                <Spinner size="lg" />
              </div>
            ) : (
              <div
                ref={trendingRef}
                className="scrollbar-hide flex gap-4 overflow-x-auto scroll-smooth px-4 lg:px-8"
                style={{ scrollSnapType: "x mandatory" }}
              >
                {result.items.slice(0, 8).map((hotel) => (
                  <div
                    key={hotel.id}
                    className="w-72 flex-shrink-0"
                    style={{ scrollSnapAlign: "start" }}
                  >
                    <HotelCard hotel={hotel} />
                  </div>
                ))}
                {result.items.length === 0 && !loading && (
                  <p className="px-4 text-muted">{tr.myBookings.empty}</p>
                )}
              </div>
            )}
          </motion.section>

          {/* ── TESTIMONIALS ── */}
          <motion.section
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mx-auto max-w-7xl px-4 py-16 lg:px-8"
          >
            <h2
              className="mb-2 text-center text-3xl font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {tr.home.testimonialsTitle}
            </h2>
            <p className="mb-10 text-center text-sm text-muted">
              {tr.home.heroSubtitle}
            </p>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {tr.home.testimonials.map((item, i) => (
                <div
                  key={i}
                  className={`rounded-2xl p-6 ${
                    i === 1
                      ? "bg-brand text-on-brand"
                      : "border border-divider bg-card text-ink"
                  }`}
                >
                  <p className={`text-sm leading-relaxed ${i === 1 ? "opacity-90" : "text-muted"}`}>
                    "{item.text}"
                  </p>
                  <div className="mt-5 flex items-center gap-3">
                    <div className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold ${i === 1 ? "bg-white/20 text-on-brand" : "bg-secondary text-muted"}`}>
                      {item.name[0]}
                    </div>
                    <div>
                      <p className={`text-sm font-semibold ${i === 1 ? "text-on-brand" : "text-ink"}`}>{item.name}</p>
                      <p className={`text-xs ${i === 1 ? "opacity-70" : "text-subtle"}`}>{item.city}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.section>

          {/* ── FOOTER CTA ── */}
          <section className="relative overflow-hidden">
            <img
              src="https://images.unsplash.com/photo-1757439402375-2f2a4ab0dc75?w=1800&q=85&auto=format&fit=crop"
              alt="Hotel exterior"
              className="h-72 w-full object-cover"
            />
            <div className="absolute inset-0 bg-black/55" />
            <div className="absolute inset-0 flex items-center justify-between px-8 lg:px-16">
              <div className="max-w-lg">
                <h2
                  className="text-3xl font-black leading-tight text-white md:text-4xl"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  {tr.home.footerCta.title}
                </h2>
                <p className="mt-2 text-sm text-gray-300">{tr.home.footerCta.subtitle}</p>
              </div>
              <Link
                to="/"
                className="hidden flex-shrink-0 rounded-full bg-white px-6 py-3 text-sm font-semibold text-gray-900 transition-colors hover:bg-gray-100 md:block"
              >
                {tr.home.footerCta.button}
              </Link>
            </div>
          </section>
        </>
      )}

      {/* ── ALL HOTELS (no search active) ── */}
      {!hasSearch && (
        <section className="mx-auto max-w-7xl px-4 py-16 lg:px-8">
          <div className="mb-6 flex items-center justify-between">
            <h2
              className="text-3xl font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {tr.home.trendingTitle}
            </h2>
            <SortControls />
          </div>

          {loading ? (
            <div className="flex justify-center py-16">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600 dark:border-red-900 dark:bg-red-900/20 dark:text-red-400">{error}</div>
          ) : (
            <>
              <HotelGrid hotels={result.items} />
              <div className="mt-8">
                <Pagination
                  page={page}
                  pages={result.pages}
                  hasNext={result.has_next}
                  hasPrev={result.has_prev}
                  onPageChange={setPage}
                />
              </div>
            </>
          )}
        </section>
      )}
    </div>
  );
}
