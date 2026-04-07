import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router";
import { imagesApi } from "../../api/images";
import { hotelsApi } from "../../api/hotels";
import { Button } from "../../components/ui/Button";
import { Spinner } from "../../components/ui/Spinner";
import { ApiError } from "../../api/client";
import type { Hotel } from "../../types/hotel";
import type { HotelImage } from "../../types/image";

export function ImagesAdmin() {
  const { hotelId } = useParams<{ hotelId: string }>();
  const navigate = useNavigate();
  const hId = Number(hotelId);
  const fileRef = useRef<HTMLInputElement>(null);

  const [hotel, setHotel] = useState<Hotel | null>(null);
  const [images, setImages] = useState<HotelImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [hotelData, imagesData] = await Promise.all([
        hotelsApi.getById(hId),
        imagesApi.getByHotel(hId),
      ]);
      setHotel(hotelData);
      setImages(imagesData);
    } catch {
      setError("Не удалось загрузить данные");
    } finally {
      setLoading(false);
    }
  }, [hId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      await imagesApi.upload(hId, file);
      await fetchData();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Ошибка загрузки"
      );
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 px-8 py-8">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <button
          onClick={() => navigate("/admin/hotels")}
          className="inline-flex w-fit items-center gap-2 text-muted hover:text-ink transition-colors"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          <span className="text-sm font-medium">Назад к отелям</span>
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black uppercase tracking-tight text-ink">
              Фотографии
            </h1>
            <p className="mt-2 text-sm text-muted">
              {hotel?.title} · {hotel?.city}
            </p>
          </div>
          <div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={handleUpload}
              className="hidden"
            />
            <Button
              loading={uploading}
              onClick={() => fileRef.current?.click()}
              className="flex items-center gap-2 bg-brand text-on-brand hover:bg-brand-hv shrink-0"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              Загрузить фото
            </Button>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="rounded-lg border border-fail/20 bg-fail/5 p-4 text-fail">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <p className="font-medium">Ошибка</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {images.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-divider bg-secondary/30 py-16">
          <svg
            className="h-12 w-12 text-subtle mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-ink mb-1">
            Нет фотографий
          </h3>
          <p className="text-muted text-sm mb-4">
            Загрузите первое фото отеля
          </p>
          <Button
            onClick={() => fileRef.current?.click()}
            className="bg-brand text-on-brand hover:bg-brand-hv"
          >
            Загрузить фото
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {images.map((img) => (
            <div
              key={img.id}
              className="group relative overflow-hidden rounded-lg bg-secondary aspect-square"
              onMouseEnter={() => setHoveredId(img.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <img
                src={`/static/images/${img.filename}`}
                alt={`Фото ${img.id}`}
                className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
                loading="lazy"
              />

              {/* Overlay */}
              <div
                className={`absolute inset-0 bg-black/50 flex flex-col items-center justify-center transition-opacity duration-200 ${
                  hoveredId === img.id ? "opacity-100" : "opacity-0"
                }`}
              >
                <div className="text-center space-y-2">
                  <p className="text-xs text-on-brand font-medium">
                    {img.filename}
                  </p>
                  <p className="text-xs text-on-brand/70">ID: {img.id}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
