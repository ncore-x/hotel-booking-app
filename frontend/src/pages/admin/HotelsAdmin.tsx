import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router";
import { hotelsApi } from "../../api/hotels";
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

  const [showModal, setShowModal] = useState(false);
  const [editingHotel, setEditingHotel] = useState<Hotel | null>(null);
  const [formTitle, setFormTitle] = useState("");
  const [formLocation, setFormLocation] = useState("");
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
    setFormLocation("");
    setFormError(null);
    setShowModal(true);
  };

  const openEdit = (hotel: Hotel) => {
    setEditingHotel(hotel);
    setFormTitle(hotel.title);
    setFormLocation(hotel.location);
    setFormError(null);
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!formTitle.trim() || !formLocation.trim()) {
      setFormError("Заполните все поля");
      return;
    }
    setSaving(true);
    setFormError(null);
    const data: HotelAddRequest = {
      title: formTitle.trim(),
      location: formLocation.trim(),
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

  return (
    <div className="flex flex-col gap-6 px-8 py-8">
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
          <div className="space-y-3">
            {hotels.map((hotel) => (
              <Card
                key={hotel.id}
                className="hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between gap-4">
                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="inline-flex items-center rounded-full bg-brand/10 px-2.5 py-0.5 text-xs font-medium text-brand">
                        ID {hotel.id}
                      </span>
                    </div>
                    <h3 className="text-sm font-semibold text-ink truncate">
                      {hotel.title}
                    </h3>
                    <p className="text-sm text-muted mt-1">{hotel.location}</p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <Link to={`/admin/hotels/${hotel.id}/rooms`}>
                      <button
                        className="p-2 rounded-lg text-muted hover:text-ink hover:bg-secondary transition-colors"
                        title="Номера"
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
                            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                          />
                        </svg>
                      </button>
                    </Link>
                    <Link to={`/admin/hotels/${hotel.id}/images`}>
                      <button
                        className="p-2 rounded-lg text-muted hover:text-ink hover:bg-secondary transition-colors"
                        title="Фотографии"
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
                      </button>
                    </Link>
                    <button
                      onClick={() => openEdit(hotel)}
                      className="p-2 rounded-lg text-muted hover:text-ink hover:bg-secondary transition-colors"
                      title="Редактировать"
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
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                        />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleDelete(hotel.id)}
                      className="p-2 rounded-lg text-muted hover:text-fail hover:bg-fail/5 transition-colors"
                      title="Удалить"
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
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </div>
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
            value={formLocation}
            onChange={(e) => setFormLocation(e.target.value)}
            placeholder="e.g. Moscow"
            required
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
