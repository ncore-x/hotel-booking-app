import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router";
import { hotelsApi } from "../api/hotels";
import { roomsApi } from "../api/rooms";
import { imagesApi } from "../api/images";
import { useSearchStore } from "../stores/searchStore";
import { useBookingStore } from "../stores/bookingStore";
import { useAuthStore } from "../stores/authStore";
import { ImageGallery } from "../components/hotel/ImageGallery";
import { RoomCard } from "../components/room/RoomCard";
import { Spinner } from "../components/ui/Spinner";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import type { Hotel } from "../types/hotel";
import type { Room } from "../types/room";
import type { HotelImage } from "../types/image";

export function HotelDetailPage() {
  const { hotelId } = useParams<{ hotelId: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
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
      setError("Отель не найден");
      setLoading(false);
      return;
    }

    if (!dateFrom || !dateTo || dateTo <= dateFrom) return;

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
        if (!cancelled) setError("Не удалось загрузить данные отеля");
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
    navigate(`/hotels/${id}/book/${roomId}`);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !hotel) {
    return (
      <div className="py-16 text-center">
        <p className="text-lg text-red-500">{error || "Отель не найден"}</p>
        <Button variant="secondary" className="mt-4" onClick={() => navigate("/")}>
          Назад к поиску
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <button
          onClick={() => navigate("/")}
          className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
          Назад к поиску
        </button>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          {hotel.title}
        </h1>
        <p className="mt-1 text-lg text-gray-500 dark:text-gray-400">
          {hotel.location}
        </p>
      </div>

      <ImageGallery images={images} />

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Доступные номера
        </h2>

        <div className="flex flex-wrap items-end gap-3">
          <Input
            label="Заезд"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
          <Input
            label="Выезд"
            type="date"
            value={dateTo}
            min={dateFrom}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>

        {rooms.length === 0 ? (
          <p className="py-8 text-center text-gray-500 dark:text-gray-400">
            Нет доступных номеров на выбранные даты
          </p>
        ) : (
          <div className="space-y-4">
            {rooms.map((room) => (
              <RoomCard key={room.id} room={room} onBook={handleBook} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
