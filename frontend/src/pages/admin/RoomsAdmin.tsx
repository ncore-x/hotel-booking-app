import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router";
import { roomsApi } from "../../api/rooms";
import { hotelsApi } from "../../api/hotels";
import { facilitiesApi } from "../../api/facilities";
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
        roomsApi.getByHotel(hId, { per_page: 50 }),
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
  }, [hId]);

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
    if (!formTitle.trim()) {
      setFormError("Введите название номера");
      return;
    }
    const price = Number(formPrice);
    const quantity = Number(formQuantity);
    if (!price || price <= 0) {
      setFormError("Цена должна быть больше нуля");
      return;
    }
    if (!quantity || quantity <= 0 || !Number.isInteger(quantity)) {
      setFormError("Количество должно быть целым числом больше нуля");
      return;
    }
    setSaving(true);
    setFormError(null);
    const data: RoomAddRequest = {
      title: formTitle.trim(),
      description: formDescription.trim() || undefined,
      price,
      quantity,
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
      setFormError(
        e instanceof ApiError ? e.detail : "Ошибка сохранения"
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (roomId: number) => {
    if (
      !window.confirm(
        "Удалить номер? Это действие нельзя отменить."
      )
    )
      return;
    try {
      await roomsApi.delete(hId, roomId);
      await fetchData();
    } catch (e) {
      setError(
        e instanceof ApiError ? e.detail : "Ошибка удаления"
      );
    }
  };

  const toggleFacility = (id: number) => {
    setFormFacilities((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id],
    );
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
              Номера
            </h1>
            <p className="mt-2 text-sm text-muted">
              {hotel?.title} · {hotel?.location}
            </p>
          </div>
          <Button
            onClick={openCreate}
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
                d="M12 4v16m8-8H4"
              />
            </svg>
            Добавить номер
          </Button>
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
      {rooms.length === 0 ? (
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
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-ink mb-1">
            Нет номеров
          </h3>
          <p className="text-muted text-sm mb-4">
            Добавьте первый номер в этот отель
          </p>
          <Button
            onClick={openCreate}
            className="bg-brand text-on-brand hover:bg-brand-hv"
          >
            Добавить номер
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {rooms.map((room) => (
            <Card key={room.id} className="hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-4">
                {/* Info */}
                <div className="flex-1 min-w-0 space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-semibold text-ink">
                      {room.title}
                    </h3>
                    <span className="inline-flex items-center rounded-full bg-brand/10 px-2.5 py-0.5 text-xs font-medium text-brand">
                      ID {room.id}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-sm">
                    <div className="flex items-center gap-1">
                      <span className="text-muted">Цена:</span>
                      <span className="font-semibold text-ink">
                        {formatPrice(room.price)}/ночь
                      </span>
                    </div>
                    <div className="w-px h-4 bg-divider" />
                    <div className="flex items-center gap-1">
                      <span className="text-muted">Кол-во:</span>
                      <span className="font-semibold text-ink">
                        {room.quantity}
                      </span>
                    </div>
                  </div>

                  {room.description && (
                    <p className="text-sm text-muted line-clamp-2">
                      {room.description}
                    </p>
                  )}

                  {room.facilities.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {room.facilities.map((f) => (
                        <FacilityBadge
                          key={f.id}
                          facility={f}
                        />
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => openEdit(room)}
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
                    onClick={() => handleDelete(room.id)}
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
      )}

      {/* Modal */}
      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title={editingRoom ? "Редактировать номер" : "Новый номер"}
      >
        <div className="space-y-4">
          <Input
            label="Название номера"
            value={formTitle}
            onChange={(e) => setFormTitle(e.target.value)}
            placeholder="e.g. Двухместный номер с видом на город"
            required
          />
          <Input
            label="Описание"
            value={formDescription}
            onChange={(e) => setFormDescription(e.target.value)}
            placeholder="Опишите номер (необязательно)"
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Цена за ночь (₽)"
              type="number"
              value={formPrice}
              onChange={(e) => setFormPrice(e.target.value)}
              placeholder="5000"
              required
            />
            <Input
              label="Количество номеров"
              type="number"
              value={formQuantity}
              onChange={(e) => setFormQuantity(e.target.value)}
              placeholder="5"
              required
            />
          </div>

          {allFacilities.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-ink mb-3">
                Удобства
              </label>
              <div className="flex flex-wrap gap-2">
                {allFacilities.map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => toggleFacility(f.id)}
                    className={`inline-flex items-center rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
                      formFacilities.includes(f.id)
                        ? "bg-brand text-on-brand shadow-sm"
                        : "bg-secondary text-muted hover:bg-secondary hover:text-ink"
                    }`}
                  >
                    {formFacilities.includes(f.id) && (
                      <svg
                        className="h-3 w-3 mr-1"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                    {f.title}
                  </button>
                ))}
              </div>
            </div>
          )}

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
              {editingRoom ? "Сохранить" : "Создать"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
