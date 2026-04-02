import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router";
import { roomsApi } from "../../api/rooms";
import { hotelsApi } from "../../api/hotels";
import { facilitiesApi } from "../../api/facilities";
import { useSearchStore } from "../../stores/searchStore";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Card } from "../../components/ui/Card";
import { Spinner } from "../../components/ui/Spinner";
import { Modal } from "../../components/ui/Modal";
import { FacilityBadge } from "../../components/room/FacilityBadge";
import { formatPrice } from "../../lib/currency";
import { ApiError } from "../../api/client";
import type { Room, RoomAddRequest } from "../../types/room";
import type { Hotel } from "../../types/hotel";
import type { Facility } from "../../types/facility";

export function RoomsAdmin() {
  const { hotelId } = useParams<{ hotelId: string }>();
  const navigate = useNavigate();
  const { dateFrom, dateTo } = useSearchStore();
  const hId = Number(hotelId);

  const [hotel, setHotel] = useState<Hotel | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [allFacilities, setAllFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showModal, setShowModal] = useState(false);
  const [editingRoom, setEditingRoom] = useState<Room | null>(null);
  const [formTitle, setFormTitle] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formPrice, setFormPrice] = useState("");
  const [formQuantity, setFormQuantity] = useState("");
  const [formFacilities, setFormFacilities] = useState<number[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [hotelData, roomsData, facilitiesData] = await Promise.all([
        hotelsApi.getById(hId),
        roomsApi.getByHotel(hId, { date_from: dateFrom, date_to: dateTo, per_page: 50 }),
        facilitiesApi.getAll({ per_page: 100 }),
      ]);
      setHotel(hotelData);
      setRooms(roomsData.items);
      setAllFacilities(facilitiesData.items);
    } catch {
      setError("Не удалось загрузить данные");
    } finally {
      setLoading(false);
    }
  }, [hId, dateFrom, dateTo]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const openCreate = () => {
    setEditingRoom(null);
    setFormTitle("");
    setFormDescription("");
    setFormPrice("");
    setFormQuantity("");
    setFormFacilities([]);
    setFormError(null);
    setShowModal(true);
  };

  const openEdit = (room: Room) => {
    setEditingRoom(room);
    setFormTitle(room.title);
    setFormDescription(room.description || "");
    setFormPrice(String(room.price));
    setFormQuantity(String(room.quantity));
    setFormFacilities(room.facilities.map((f) => f.id));
    setFormError(null);
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);
    const data: RoomAddRequest = {
      title: formTitle,
      description: formDescription || undefined,
      price: Number(formPrice),
      quantity: Number(formQuantity),
      facilities_ids: formFacilities,
    };
    try {
      if (editingRoom) {
        await roomsApi.update(hId, editingRoom.id, data);
      } else {
        await roomsApi.create(hId, data);
      }
      setShowModal(false);
      await fetchData();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.detail : "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (roomId: number) => {
    try {
      await roomsApi.delete(hId, roomId);
      await fetchData();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Ошибка удаления");
    }
  };

  const toggleFacility = (id: number) => {
    setFormFacilities((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id],
    );
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
            Номера — {hotel?.title}
          </h2>
        </div>
        <Button size="sm" onClick={openCreate}>Добавить</Button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="space-y-3">
        {rooms.map((room) => (
          <Card key={room.id}>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="font-medium text-gray-900 dark:text-white">{room.title}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {formatPrice(room.price)} / ночь &middot; {room.quantity} шт.
                </p>
                {room.facilities.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {room.facilities.map((f) => (
                      <FacilityBadge key={f.id} facility={f} />
                    ))}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => openEdit(room)}>
                  Редактировать
                </Button>
                <Button size="sm" variant="danger" onClick={() => handleDelete(room.id)}>
                  Удалить
                </Button>
              </div>
            </div>
          </Card>
        ))}
        {rooms.length === 0 && (
          <p className="py-8 text-center text-gray-500 dark:text-gray-400">Номера не добавлены</p>
        )}
      </div>

      <Modal open={showModal} onClose={() => setShowModal(false)} title={editingRoom ? "Редактировать номер" : "Новый номер"}>
        <div className="space-y-3">
          <Input label="Название" value={formTitle} onChange={(e) => setFormTitle(e.target.value)} required />
          <Input label="Описание" value={formDescription} onChange={(e) => setFormDescription(e.target.value)} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Цена за ночь" type="number" value={formPrice} onChange={(e) => setFormPrice(e.target.value)} required />
            <Input label="Количество" type="number" value={formQuantity} onChange={(e) => setFormQuantity(e.target.value)} required />
          </div>
          {allFacilities.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Удобства</p>
              <div className="flex flex-wrap gap-2">
                {allFacilities.map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => toggleFacility(f.id)}
                    className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                      formFacilities.includes(f.id)
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300"
                    }`}
                  >
                    {f.title}
                  </button>
                ))}
              </div>
            </div>
          )}
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
