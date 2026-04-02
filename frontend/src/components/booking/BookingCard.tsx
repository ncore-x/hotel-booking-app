import { useState } from "react";
import type { Booking } from "../../types/booking";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { formatDisplayDate, nightsBetween } from "../../lib/dates";
import { formatPrice } from "../../lib/currency";

interface BookingCardProps {
  booking: Booking;
  onCancel: (id: number) => Promise<void>;
  onUpdate: (id: number, dateFrom: string, dateTo: string) => Promise<void>;
}

export function BookingCard({ booking, onCancel, onUpdate }: BookingCardProps) {
  const [editing, setEditing] = useState(false);
  const [newDateFrom, setNewDateFrom] = useState(booking.date_from);
  const [newDateTo, setNewDateTo] = useState(booking.date_to);
  const [loading, setLoading] = useState(false);

  const nights = nightsBetween(booking.date_from, booking.date_to);

  const handleCancel = async () => {
    setLoading(true);
    try {
      await onCancel(booking.id);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    setLoading(true);
    try {
      await onUpdate(booking.id, newDateFrom, newDateTo);
      setEditing(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <div className="space-y-3">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Бронирование #{booking.id}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Номер #{booking.room_id}
            </p>
          </div>
          <p className="text-lg font-bold text-gray-900 dark:text-white">
            {formatPrice(booking.price)}
          </p>
        </div>

        {editing ? (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-3">
              <Input
                label="Заезд"
                type="date"
                value={newDateFrom}
                onChange={(e) => setNewDateFrom(e.target.value)}
              />
              <Input
                label="Выезд"
                type="date"
                value={newDateTo}
                min={newDateFrom}
                onChange={(e) => setNewDateTo(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" loading={loading} onClick={handleUpdate}>
                Сохранить
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  setEditing(false);
                  setNewDateFrom(booking.date_from);
                  setNewDateTo(booking.date_to);
                }}
              >
                Отмена
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
              <span className="text-gray-500 dark:text-gray-400">
                Заезд: <span className="text-gray-900 dark:text-white">{formatDisplayDate(booking.date_from)}</span>
              </span>
              <span className="text-gray-500 dark:text-gray-400">
                Выезд: <span className="text-gray-900 dark:text-white">{formatDisplayDate(booking.date_to)}</span>
              </span>
              <span className="text-gray-500 dark:text-gray-400">
                Ночей: <span className="text-gray-900 dark:text-white">{nights}</span>
              </span>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>
                Изменить даты
              </Button>
              <Button size="sm" variant="danger" loading={loading} onClick={handleCancel}>
                Отменить
              </Button>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}
