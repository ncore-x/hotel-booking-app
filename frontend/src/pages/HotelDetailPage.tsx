import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router";
import { addDays } from "date-fns";
import { hotelsApi } from "../api/hotels";
import { roomsApi } from "../api/rooms";
import { imagesApi } from "../api/images";
import { formatDate } from "../lib/dates";
import { useSearchStore } from "../stores/searchStore";
import { useBookingStore } from "../stores/bookingStore";
import { useAuthStore } from "../stores/authStore";
import { ImageGallery } from "../components/hotel/ImageGallery";
import { RoomCard } from "../components/room/RoomCard";
import { Spinner } from "../components/ui/Spinner";
import { Input } from "../components/ui/Input";
import { useT } from "../i18n/useT";
import type { Hotel } from "../types/hotel";
import type { Room } from "../types/room";
import type { HotelImage } from "../types/image";

export function HotelDetailPage() {
  const { hotelId } = useParams<{ hotelId: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const t = useT();
  const { dateFrom: searchDateFrom, dateTo: searchDateTo } = useSearchStore();
  const { setRoom, setDates } = useBookingStore();

  const [hotel, setHotel] = useState<Hotel | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [images, setImages] = useState<HotelImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [dateFrom, setDateFrom] = useState(searchDateFrom);
  const [dateTo, setDateTo] = useState(searchDateTo);

  const id = Number(hotelId);

  useEffect(() => {
    if (!id || isNaN(id)) {
      setError(t.common.notFound);
      setLoading(false);
      return;
    }
    if (!dateFrom || !dateTo || dateTo <= dateFrom) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      hotelsApi.getById(id),
      roomsApi.getByHotel(id, { date_from: dateFrom, date_to: dateTo, per_page: 50 }),
      imagesApi.getByHotel(id),
    ])
      .then(([hotelData, roomsData, imagesData]) => {
        if (cancelled) return;
        setHotel(hotelData);
        setRooms(roomsData.items);
        setImages(imagesData);
      })
      .catch(() => {
        if (!cancelled) setError(t.common.error);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [id, dateFrom, dateTo]);

  const handleBook = (roomId: number) => {
    if (!user) {
      navigate("/login");
      return;
    }
    setRoom(id, roomId);
    setDates(dateFrom, dateTo);
    navigate(`/hotels/${id}/book/${roomId}?from=${encodeURIComponent(dateFrom)}&to=${encodeURIComponent(dateTo)}`);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !hotel) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <p className="text-lg font-semibold text-red-500">{error || t.common.notFound}</p>
        <button
          onClick={() => navigate("/")}
          className="mt-4 rounded-xl border border-divider px-5 py-2.5 text-sm font-medium text-muted transition-colors hover:border-ink hover:text-ink"
        >
          ← {t.hotelDetail.backToSearch}
        </button>
      </div>
    );
  }

  return (
    <div className="bg-surface">
      {/* Gallery hero */}
      {images.length > 0 && (
        <div className="mx-auto max-w-7xl px-4 pt-8 lg:px-8">
          <ImageGallery images={images} />
        </div>
      )}

      <div className="mx-auto max-w-7xl px-4 py-10 lg:px-8">
        {/* Back link */}
        <button
          onClick={() => navigate("/")}
          className="mb-6 flex items-center gap-1.5 text-sm font-medium text-muted transition-colors hover:text-ink"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
          {t.hotelDetail.backToSearch}
        </button>

        <div className="flex flex-col gap-10 lg:flex-row">
          {/* Left — hotel info + rooms */}
          <div className="flex-1 min-w-0">
            <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-xs font-semibold text-muted">
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
              </svg>
              {hotel.city}{hotel.address ? `, ${hotel.address}` : ""}
            </div>

            <h1
              className="mb-8 text-4xl font-black tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {hotel.title}
            </h1>

            {/* Rooms section */}
            <div>
              <h2
                className="mb-6 text-xl font-black uppercase tracking-tight text-ink"
                style={{ fontFamily: "var(--font-display)" }}
              >
                {t.hotelDetail.availableRooms}
              </h2>

              {rooms.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-divider py-12 text-center">
                  <p className="text-muted">
                    {t.hotelDetail.noRooms}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {rooms.map((room) => (
                    <RoomCard key={room.id} room={room} onBook={handleBook} />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right — sticky booking widget */}
          <div className="w-full lg:w-80 lg:flex-shrink-0">
            <div className="sticky top-24 rounded-2xl border border-divider bg-card p-6 shadow-sm">
              <h3 className="mb-5 text-base font-bold text-ink">
                {t.hotelDetail.selectDates}
              </h3>

              <div className="space-y-4">
                <Input
                  label={t.hotelDetail.checkIn}
                  type="date"
                  value={dateFrom}
                  onChange={(e) => {
                    const newFrom = e.target.value;
                    if (newFrom >= dateTo) setDateTo(formatDate(addDays(new Date(newFrom + "T00:00:00"), 1)));
                    setDateFrom(newFrom);
                  }}
                />
                <Input
                  label={t.hotelDetail.checkOut}
                  type="date"
                  value={dateTo}
                  min={formatDate(addDays(new Date(dateFrom + "T00:00:00"), 1))}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>

              {dateFrom && dateTo && dateTo > dateFrom && (
                <div className="mt-4 rounded-xl bg-secondary p-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted">{t.hotelDetail.nights}</span>
                    <span className="font-semibold text-ink">
                      {Math.round(
                        (new Date(dateTo).getTime() - new Date(dateFrom).getTime()) /
                          86400000,
                      )}
                    </span>
                  </div>
                </div>
              )}

              <p className="mt-4 text-center text-xs text-subtle">
                {t.hotelDetail.chooseBelowToBook}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
