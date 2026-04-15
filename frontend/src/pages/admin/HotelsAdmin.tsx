import { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router";
import { hotelsApi } from "../../api/hotels";
import { imagesApi } from "../../api/images";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Card } from "../../components/ui/Card";
import { Spinner } from "../../components/ui/Spinner";
import { Modal } from "../../components/ui/Modal";
import { Pagination } from "../../components/Pagination";
import { ApiError } from "../../api/client";
import type { Hotel, HotelAddRequest } from "../../types/hotel";

export function HotelsAdmin() {
  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadTargetId = useRef<number | null>(null);

  const [showModal, setShowModal] = useState(false);
  const [editingHotel, setEditingHotel] = useState<Hotel | null>(null);
  const [formTitle, setFormTitle] = useState("");
  const [formCity, setFormCity] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchHotels = useCallback(async () => {
    setLoading(true);
    try {
      const res = await hotelsApi.search({
        page,
        per_page: 20,
      });
      setHotels(res.items);
      setPages(res.pages);
      setHasNext(res.has_next);
      setHasPrev(res.has_prev);
    } catch {
      setError("Не удалось загрузить отели");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchHotels();
  }, [fetchHotels]);

  const openCreate = () => {
    setEditingHotel(null);
    setFormTitle("");
    setFormCity("");
    setFormAddress("");
    setFormError(null);
    setShowModal(true);
  };

  const openEdit = (hotel: Hotel) => {
    setEditingHotel(hotel);
    setFormTitle(hotel.title);
    setFormCity(hotel.city);
    setFormAddress(hotel.address || "");
    setFormError(null);
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!formTitle.trim() || !formCity.trim()) {
      setFormError("Заполните название и город");
      return;
    }
    setSaving(true);
    setFormError(null);
    const data: HotelAddRequest = {
      title: formTitle.trim(),
      city: formCity.trim(),
      address: formAddress.trim() || undefined,
    };
    try {
      if (editingHotel) {
        await hotelsApi.update(editingHotel.id, data);
      } else {
        await hotelsApi.create(data);
      }
      setShowModal(false);
      await fetchHotels();
    } catch (e) {
      setFormError(
        e instanceof ApiError ? e.detail : "Ошибка сохранения"
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (
      !window.confirm(
        "Удалить отель? Это действие нельзя отменить."
      )
    )
      return;
    try {
      await hotelsApi.delete(id);
      await fetchHotels();
    } catch (e) {
      setError(
        e instanceof ApiError ? e.detail : "Ошибка удаления"
      );
    }
  };

  const handleAvatarClick = (hotelId: number) => {
    uploadTargetId.current = hotelId;
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    const hotelId = uploadTargetId.current;
    if (!file || !hotelId) return;
    e.target.value = "";
    setUploadingId(hotelId);
    try {
      await imagesApi.upload(hotelId, file);
      await fetchHotels();
    } catch {
      setError("Не удалось загрузить фото");
    } finally {
      setUploadingId(null);
    }
  };

  return (
    <div className="flex flex-col gap-6 px-8 py-8">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black uppercase tracking-tight text-ink">
            Отели
          </h1>
          <p className="mt-1 text-sm text-muted">
            Управление список всеми отелями в системе
          </p>
        </div>
        <Button
          onClick={openCreate}
          className="flex items-center gap-2 bg-brand text-on-brand hover:bg-brand-hv"
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
              d="M12 4v16m8-8H4"
            />
          </svg>
          Добавить отель
        </Button>
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
      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : hotels.length === 0 ? (
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
              d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-ink mb-1">Нет отелей</h3>
          <p className="text-muted text-sm mb-4">
            Добавьте первый отель, чтобы начать работу
          </p>
          <Button
            onClick={openCreate}
            className="bg-brand text-on-brand hover:bg-brand-hv"
          >
            Добавить отель
          </Button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7">
            {hotels.map((hotel) => (
              <Card
                key={hotel.id}
                className="flex flex-col overflow-hidden p-0 hover:shadow-md transition-shadow"
              >
                {/* Cover image */}
                <div className="relative h-24 w-full bg-secondary shrink-0">
                  {hotel.cover_image_url ? (
                    <img
                      src={hotel.cover_image_url}
                      alt={hotel.title}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center">
                      <svg className="h-6 w-6 text-subtle" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 0h.008v.008h-.008V7.5z" />
                      </svg>
                    </div>
                  )}
                  <span className="absolute top-1.5 left-1.5 inline-flex items-center rounded-full bg-black/55 px-1.5 py-px text-[10px] font-semibold text-white backdrop-blur-sm">
                    ID {hotel.id}
                  </span>
                </div>

                {/* Info */}
                <div className="flex flex-1 flex-col gap-0.5 px-2 py-1.5">
                  <h3 className="text-xs font-semibold text-ink leading-tight line-clamp-2">
                    {hotel.title}
                  </h3>
                  <p className="text-[10px] text-muted truncate leading-tight">
                    {hotel.city}{hotel.address ? `, ${hotel.address}` : ""}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between border-t border-divider px-1 py-1">
                  <button
                    onClick={() => handleAvatarClick(hotel.id)}
                    disabled={uploadingId === hotel.id}
                    className="p-1 rounded text-muted hover:text-ink hover:bg-secondary transition-colors disabled:opacity-50"
                    title="Загрузить обложку"
                  >
                    {uploadingId === hotel.id ? (
                      <Spinner size="sm" />
                    ) : (
                      <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </button>
                  <Link to={`/admin/hotels/${hotel.id}/rooms`}>
                    <button className="p-1 rounded text-muted hover:text-ink hover:bg-secondary transition-colors" title="Номера">
                      <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </Link>
                  <Link to={`/admin/hotels/${hotel.id}/images`}>
                    <button className="p-1 rounded text-muted hover:text-ink hover:bg-secondary transition-colors" title="Фотографии">
                      <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </Link>
                  <button
                    onClick={() => openEdit(hotel)}
                    className="p-1 rounded text-muted hover:text-ink hover:bg-secondary transition-colors"
                    title="Редактировать"
                  >
                    <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(hotel.id)}
                    className="p-1 rounded text-muted hover:text-fail hover:bg-fail/5 transition-colors"
                    title="Удалить"
                  >
                    <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-center">
            <Pagination
              page={page}
              pages={pages}
              hasNext={hasNext}
              hasPrev={hasPrev}
              onPageChange={setPage}
            />
          </div>
        </>
      )}

      {/* Modal */}
      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title={editingHotel ? "Редактировать отель" : "Новый отель"}
      >
        <div className="space-y-4">
          <Input
            label="Название отеля"
            value={formTitle}
            onChange={(e) => setFormTitle(e.target.value)}
            placeholder="e.g. Grand Hotel Moscow"
            required
          />
          <Input
            label="Город"
            value={formCity}
            onChange={(e) => setFormCity(e.target.value)}
            placeholder="Москва"
            required
          />
          <Input
            label="Адрес (необязательно)"
            value={formAddress}
            onChange={(e) => setFormAddress(e.target.value)}
            placeholder="ул. Тверская, 1"
          />

          {formError && (
            <div className="rounded-lg border border-fail/20 bg-fail/5 p-3 text-sm text-fail">
              {formError}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button
              variant="secondary"
              onClick={() => setShowModal(false)}
              className="text-muted hover:text-ink"
            >
              Отмена
            </Button>
            <Button
              loading={saving}
              onClick={handleSave}
              className="bg-brand text-on-brand hover:bg-brand-hv"
            >
              {editingHotel ? "Сохранить" : "Создать"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
