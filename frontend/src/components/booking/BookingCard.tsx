import { useState } from "react";
import type { Booking } from "../../types/booking";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { formatDisplayDate, nightsBetween, getDefaultDateFrom } from "../../lib/dates";
import { formatPrice } from "../../lib/currency";
import { useT } from "../../i18n/useT";

interface BookingCardProps {
  booking: Booking;
  onCancel: (id: number) => Promise<void>;
  onUpdate: (id: number, dateFrom: string, dateTo: string) => Promise<void>;
}

function getBookingStatus(dateFrom: string, dateTo: string): "upcoming" | "active" | "completed" {
  const now = new Date().toISOString().split("T")[0];
  if (dateTo < now) return "completed";
  if (dateFrom <= now) return "active";
  return "upcoming";
}

export function BookingCard({ booking, onCancel, onUpdate }: BookingCardProps) {
  const [editing, setEditing] = useState(false);
  const [newDateFrom, setNewDateFrom] = useState(booking.date_from);
  const [newDateTo, setNewDateTo] = useState(booking.date_to);
  const [loading, setLoading] = useState(false);
  const t = useT();

  const today = getDefaultDateFrom();
  const nights = nightsBetween(booking.date_from, booking.date_to);
  const totalCost = booking.total_cost ?? booking.price * nights;
  const status = getBookingStatus(booking.date_from, booking.date_to);
  const isCompleted = status === "completed";

  const statusConfig = {
    upcoming: { label: t.bookingCard.status.upcoming, cls: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" },
    active: { label: t.bookingCard.status.active, cls: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" },
    completed: { label: t.bookingCard.status.completed, cls: "bg-secondary text-muted" },
  };

  const handleCancel = async () => {
    setLoading(true);
    try {
      await onCancel(booking.id);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!newDateFrom || !newDateTo || newDateTo <= newDateFrom) return;
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
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs text-subtle">#{booking.id} · Room #{booking.room_id}</p>
            <span className={`mt-1 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusConfig[status].cls}`}>
              {statusConfig[status].label}
            </span>
          </div>
          <div className="flex-shrink-0 text-right">
            <p className="text-xs text-muted">{t.bookingCard.perNightLabel} {formatPrice(booking.price)}</p>
            <p className="text-lg font-bold text-ink">{formatPrice(totalCost)}</p>
            <p className="text-xs text-muted">{t.bookingCard.totalLabel}</p>
          </div>
        </div>

        {editing ? (
          <div className="space-y-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Input
                label={t.bookingCard.checkIn}
                type="date"
                value={newDateFrom}
                min={today}
                onChange={(e) => setNewDateFrom(e.target.value)}
              />
              <Input
                label={t.bookingCard.checkOut}
                type="date"
                value={newDateTo}
                min={newDateFrom}
                onChange={(e) => setNewDateTo(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" loading={loading} onClick={handleUpdate}>
                {t.profilePage.save}
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
                {t.bookingCard.cancel}
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
              <span className="text-muted">
                {t.bookingCard.checkIn}: <span className="text-ink">{formatDisplayDate(booking.date_from)}</span>
              </span>
              <span className="text-muted">
                {t.bookingCard.checkOut}: <span className="text-ink">{formatDisplayDate(booking.date_to)}</span>
              </span>
              <span className="text-muted">
                {t.bookingCard.nights(nights)}
              </span>
            </div>
            {!isCompleted && (
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>
                  {t.bookingCard.edit}
                </Button>
                <Button size="sm" variant="danger" loading={loading} onClick={handleCancel}>
                  {t.bookingCard.cancel}
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </Card>
  );
}
