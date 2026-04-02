import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router";
import { bookingsApi } from "../api/bookings";
import { useAuthStore } from "../stores/authStore";
import { BookingCard } from "../components/booking/BookingCard";
import { Pagination } from "../components/Pagination";
import { Spinner } from "../components/ui/Spinner";
import { ApiError } from "../api/client";
import type { Booking } from "../types/booking";

export function MyBookingsPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  const fetchBookings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await bookingsApi.getMy({ page, per_page: 10 });
      setBookings(res.items);
      setPages(res.pages);
      setHasNext(res.has_next);
      setHasPrev(res.has_prev);
    } catch {
      setError("Не удалось загрузить бронирования");
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
      const msg = e instanceof ApiError ? e.detail : "Не удалось отменить бронирование";
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
      const msg = e instanceof ApiError ? e.detail : "Не удалось изменить даты";
      setError(msg);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        Мои бронирования
      </h1>

      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : bookings.length === 0 ? (
        <div className="py-16 text-center text-gray-500 dark:text-gray-400">
          <p className="text-lg">У вас пока нет бронирований</p>
          <p className="mt-1 text-sm">Найдите отель и забронируйте номер</p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {bookings.map((b) => (
              <BookingCard
                key={b.id}
                booking={b}
                onCancel={handleCancel}
                onUpdate={handleUpdate}
              />
            ))}
          </div>
          <Pagination
            page={page}
            pages={pages}
            hasNext={hasNext}
            hasPrev={hasPrev}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
