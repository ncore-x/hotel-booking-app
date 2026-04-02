import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router";
import { hotelsApi } from "../../api/hotels";
import { useSearchStore } from "../../stores/searchStore";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Card } from "../../components/ui/Card";
import { Spinner } from "../../components/ui/Spinner";
import { Modal } from "../../components/ui/Modal";
import { Pagination } from "../../components/Pagination";
import { ApiError } from "../../api/client";
import type { Hotel, HotelAddRequest } from "../../types/hotel";

export function HotelsAdmin() {
  const { dateFrom, dateTo } = useSearchStore();
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
        date_from: dateFrom,
        date_to: dateTo,
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
  }, [dateFrom, dateTo, page]);

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
    setSaving(true);
    setFormError(null);
    const data: HotelAddRequest = { title: formTitle, location: formLocation };
    try {
      if (editingHotel) {
        await hotelsApi.update(editingHotel.id, data);
      } else {
        await hotelsApi.create(data);
      }
      setShowModal(false);
      await fetchHotels();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.detail : "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await hotelsApi.delete(id);
      await fetchHotels();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Ошибка удаления");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Отели</h2>
        <Button size="sm" onClick={openCreate}>Добавить</Button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {hotels.map((hotel) => (
              <Card key={hotel.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{hotel.title}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{hotel.location}</p>
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/admin/hotels/${hotel.id}/rooms`}>
                      <Button size="sm" variant="ghost">Номера</Button>
                    </Link>
                    <Link to={`/admin/hotels/${hotel.id}/images`}>
                      <Button size="sm" variant="ghost">Фото</Button>
                    </Link>
                    <Button size="sm" variant="secondary" onClick={() => openEdit(hotel)}>
                      Редактировать
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => handleDelete(hotel.id)}>
                      Удалить
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
          <Pagination page={page} pages={pages} hasNext={hasNext} hasPrev={hasPrev} onPageChange={setPage} />
        </>
      )}

      <Modal open={showModal} onClose={() => setShowModal(false)} title={editingHotel ? "Редактировать отель" : "Новый отель"}>
        <div className="space-y-3">
          <Input label="Название" value={formTitle} onChange={(e) => setFormTitle(e.target.value)} required />
          <Input label="Город" value={formLocation} onChange={(e) => setFormLocation(e.target.value)} required />
          {formError && <p className="text-sm text-red-500">{formError}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Отмена</Button>
            <Button loading={saving} onClick={handleSave}>Сохранить</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
