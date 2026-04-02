import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router";
import { useBookingStore } from "../stores/bookingStore";
import { useAuthStore } from "../stores/authStore";
import { roomsApi } from "../api/rooms";
import { hotelsApi } from "../api/hotels";
import { bookingsApi } from "../api/bookings";
import { BookingSummary } from "../components/booking/BookingSummary";
import { Spinner } from "../components/ui/Spinner";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ApiError } from "../api/client";
import type { Room } from "../types/room";
import type { Hotel } from "../types/hotel";

export function BookingConfirmPage() {
  const { hotelId, roomId } = useParams<{ hotelId: string; roomId: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { dateFrom, dateTo, reset: resetBooking } = useBookingStore();

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

    Promise.all([
      hotelsApi.getById(hId),
      roomsApi.getById(hId, rId),
    ])
      .then(([hotelData, roomData]) => {
        setHotel(hotelData);
        setRoom(roomData);
      })
      .catch(() => setError("Не удалось загрузить данные"))
      .finally(() => setLoading(false));
  }, [hId, rId, dateFrom, dateTo, user, navigate, hotelId]);

  const handleConfirm = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await bookingsApi.create({
        room_id: rId,
        date_from: dateFrom,
        date_to: dateTo,
      });
      setSuccess(true);
      resetBooking();
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : "Не удалось создать бронирование";
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
      <div className="mx-auto max-w-md pt-12 text-center">
        <Card>
          <div className="space-y-4 py-4">
            <svg className="mx-auto h-16 w-16 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Бронирование подтверждено!
            </h2>
            <p className="text-gray-500 dark:text-gray-400">
              Вы успешно забронировали номер
            </p>
            <div className="flex justify-center gap-3 pt-2">
              <Button variant="secondary" onClick={() => navigate("/bookings")}>
                Мои бронирования
              </Button>
              <Button onClick={() => navigate("/")}>
                На главную
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (error && !room) {
    return (
      <div className="py-16 text-center">
        <p className="text-lg text-red-500">{error}</p>
        <Button variant="secondary" className="mt-4" onClick={() => navigate(-1)}>
          Назад
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <button
          onClick={() => navigate(`/hotels/${hotelId}`)}
          className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
          Назад к отелю
        </button>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Подтверждение бронирования
        </h1>
        {hotel && (
          <p className="mt-1 text-gray-500 dark:text-gray-400">
            {hotel.title} — {hotel.location}
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
          Отмена
        </Button>
        <Button loading={submitting} onClick={handleConfirm}>
          Подтвердить бронирование
        </Button>
      </div>
    </div>
  );
}
