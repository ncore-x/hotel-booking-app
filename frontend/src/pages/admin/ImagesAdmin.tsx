import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router";
import { imagesApi } from "../../api/images";
import { hotelsApi } from "../../api/hotels";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
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
      setError(err instanceof ApiError ? err.detail : "Ошибка загрузки");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate("/admin/hotels")}
            className="mb-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400"
          >
            &larr; Назад к отелям
          </button>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Фото — {hotel?.title}
          </h2>
        </div>
        <div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            onChange={handleUpload}
            className="hidden"
          />
          <Button size="sm" loading={uploading} onClick={() => fileRef.current?.click()}>
            Загрузить
          </Button>
        </div>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {images.length === 0 ? (
        <Card>
          <p className="py-8 text-center text-gray-500 dark:text-gray-400">Фото не загружены</p>
        </Card>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {images.map((img) => (
            <div key={img.id} className="overflow-hidden rounded-lg">
              <img
                src={`/static/images/${img.filename}`}
                alt={`Фото ${img.id}`}
                className="h-48 w-full object-cover"
                loading="lazy"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
