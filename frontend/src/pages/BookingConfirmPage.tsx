import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router";
import { motion, AnimatePresence } from "framer-motion";
import { useBookingStore } from "../stores/bookingStore";
import { useAuthStore } from "../stores/authStore";
import { roomsApi } from "../api/rooms";
import { hotelsApi } from "../api/hotels";
import { bookingsApi } from "../api/bookings";
import { BookingSummary } from "../components/booking/BookingSummary";
import { Spinner } from "../components/ui/Spinner";
import { Button } from "../components/ui/Button";
import { ApiError } from "../api/client";
import { useT } from "../i18n/useT";
import { useNotificationStore } from "../stores/notificationStore";
import type { Room } from "../types/room";
import type { Hotel } from "../types/hotel";

export function BookingConfirmPage() {
  const { hotelId, roomId } = useParams<{ hotelId: string; roomId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const user = useAuthStore((s) => s.user);
  const { dateFrom: storeDateFrom, dateTo: storeDateTo, reset: resetBooking } = useBookingStore();
  const t = useT();
  const addNotification = useNotificationStore((s) => s.add);

  // Prefer URL params (survives refresh); fall back to store (legacy navigation)
  const dateFrom = searchParams.get("from") ?? storeDateFrom;
  const dateTo = searchParams.get("to") ?? storeDateTo;

  const [hotel, setHotel] = useState<Hotel | null>(null);
  const [room, setRoom] = useState<Room | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const hId = Number(hotelId);
  const rId = Number(roomId);

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }

    if (!dateFrom || !dateTo) {
      navigate(`/hotels/${hotelId}`);
      return;
    }

    let cancelled = false;
    Promise.all([
      hotelsApi.getById(hId),
      roomsApi.getById(hId, rId),
    ])
      .then(([hotelData, roomData]) => {
        if (cancelled) return;
        setHotel(hotelData);
        setRoom(roomData);
      })
      .catch(() => { if (!cancelled) setError(t.bookingConfirm.loadError); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [hId, rId, dateFrom, dateTo, user, navigate, hotelId]);

  useEffect(() => {
    if (!success) return;
    const timer = setTimeout(() => navigate("/bookings"), 2000);
    return () => clearTimeout(timer);
  }, [success, navigate]);

  const handleConfirm = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const booking = await bookingsApi.create({
        room_id: rId,
        date_from: dateFrom,
        date_to: dateTo,
      });
      addNotification(
        "booking_created",
        t.notifications.bookingCreatedTitle,
        t.notifications.bookingCreatedBody(
          booking.id,
          hotel?.title ?? "",
          hotel?.city ?? "",
        ),
      );
      setSuccess(true);
      resetBooking();
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : t.bookingConfirm.createError;
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (success) {
    return (
      <AnimatePresence>
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="flex flex-col items-center gap-3"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.15, type: "spring", stiffness: 250, damping: 15 }}
              className="flex h-24 w-24 items-center justify-center rounded-full bg-green-500 shadow-lg"
            >
              <svg className="h-14 w-14 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <motion.path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ delay: 0.3, duration: 0.4 }}
                />
              </svg>
            </motion.div>
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="text-lg font-semibold text-white"
            >
              {t.bookingConfirm.booked}
            </motion.p>
          </motion.div>
        </div>
      </AnimatePresence>
    );
  }

  if (error && !room) {
    return (
      <div className="py-16 text-center">
        <p className="text-lg text-red-500">{error}</p>
        <Button variant="secondary" className="mt-4" onClick={() => navigate(-1)}>
          {t.bookingConfirm.cancel}
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <button
          onClick={() => navigate(`/hotels/${hotelId}`)}
          className="mb-4 flex items-center gap-1 text-sm text-muted transition-colors hover:text-ink"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
          {t.bookingConfirm.backToHotel}
        </button>
        <h1 className="text-2xl font-bold text-ink">
          {t.bookingConfirm.title}
        </h1>
        {hotel && (
          <p className="mt-1 text-muted">
            {hotel.title} — {hotel.city}
          </p>
        )}
      </div>

      {room && (
        <BookingSummary room={room} dateFrom={dateFrom} dateTo={dateTo} />
      )}

      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}

      <div className="flex gap-3">
        <Button
          variant="secondary"
          onClick={() => navigate(`/hotels/${hotelId}`)}
        >
          {t.bookingConfirm.cancel}
        </Button>
        <Button loading={submitting} onClick={handleConfirm}>
          {t.bookingConfirm.confirm}
        </Button>
      </div>
    </div>
  );
}
