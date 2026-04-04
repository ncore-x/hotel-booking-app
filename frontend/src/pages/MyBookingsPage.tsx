import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate } from "react-router";
import { bookingsApi } from "../api/bookings";
import { useAuthStore } from "../stores/authStore";
import { useT } from "../i18n/useT";
import { BookingCard } from "../components/booking/BookingCard";
import { Pagination } from "../components/Pagination";
import { Spinner } from "../components/ui/Spinner";
import { ApiError } from "../api/client";
import type { Booking } from "../types/booking";

type Filter = "all" | "upcoming" | "active" | "completed";

function getBookingStatus(dateFrom: string, dateTo: string): "upcoming" | "active" | "completed" {
  const now = new Date().toISOString().split("T")[0];
  if (dateTo < now) return "completed";
  if (dateFrom <= now) return "active";
  return "upcoming";
}

export function MyBookingsPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const isLoading = useAuthStore((s) => s.isLoading);
  const t = useT();

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    if (!isLoading && !user) navigate("/login");
  }, [user, isLoading, navigate]);

  const fetchBookings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await bookingsApi.getMy({ page, per_page: 100 });
      setBookings(res.items);
      setPages(res.pages);
      setHasNext(res.has_next);
      setHasPrev(res.has_prev);
    } catch {
      setError(t.common.error);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    if (user) fetchBookings();
  }, [user, fetchBookings]);

  const handleCancel = async (id: number) => {
    if (actionLoading !== null) return;
    setActionLoading(id);
    try {
      await bookingsApi.cancel(id);
      await fetchBookings();
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : t.common.error;
      setError(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpdate = async (id: number, dateFrom: string, dateTo: string) => {
    if (actionLoading !== null) return;
    setActionLoading(id);
    try {
      await bookingsApi.patch(id, { date_from: dateFrom, date_to: dateTo });
      await fetchBookings();
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : t.common.error;
      setError(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const filtered = useMemo(() => {
    if (filter === "all") return bookings;
    return bookings.filter((b) => getBookingStatus(b.date_from, b.date_to) === filter);
  }, [bookings, filter]);

  const counts = useMemo(() => ({
    all: bookings.length,
    upcoming: bookings.filter((b) => getBookingStatus(b.date_from, b.date_to) === "upcoming").length,
    active: bookings.filter((b) => getBookingStatus(b.date_from, b.date_to) === "active").length,
    completed: bookings.filter((b) => getBookingStatus(b.date_from, b.date_to) === "completed").length,
  }), [bookings]);

  const tabs: { key: Filter; label: string }[] = [
    { key: "all", label: t.myBookings.all },
    { key: "upcoming", label: t.myBookings.upcoming },
    { key: "active", label: t.myBookings.active },
    { key: "completed", label: t.myBookings.completed },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 lg:px-8">
      {/* Header */}
      <div className="mb-8 border-b border-divider pb-6">
        <h1
          className="text-4xl font-black uppercase tracking-tight text-ink"
          style={{ fontFamily: "var(--font-display)" }}
        >
          {t.myBookings.title}
        </h1>
      </div>

      {/* Filter tabs */}
      {!loading && bookings.length > 0 && (
        <div className="mb-6 flex gap-2">
          {tabs.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                filter === key
                  ? "bg-brand text-on-brand"
                  : "border border-divider text-muted hover:border-ink hover:text-ink"
              }`}
            >
              {label}
              {counts[key] > 0 && (
                <span className={`ml-1.5 text-xs ${filter === key ? "opacity-80" : "opacity-60"}`}>
                  {counts[key]}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600 dark:border-red-900 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
            <svg className="h-8 w-8 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
            </svg>
          </div>
          <p className="text-lg font-semibold text-ink">{t.myBookings.empty}</p>
          <p className="mt-1 text-sm text-muted">{t.myBookings.emptySubtitle}</p>
          {filter === "all" && (
            <button
              onClick={() => navigate("/")}
              className="mt-6 rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv"
            >
              {t.myBookings.browseHotels}
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {filtered.map((b) => (
              <BookingCard
                key={b.id}
                booking={b}
                onCancel={handleCancel}
                onUpdate={handleUpdate}
              />
            ))}
          </div>
          {filter === "all" && (
            <div className="mt-8">
              <Pagination
                page={page}
                pages={pages}
                hasNext={hasNext}
                hasPrev={hasPrev}
                onPageChange={setPage}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
