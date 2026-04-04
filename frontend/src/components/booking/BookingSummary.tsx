import type { Room } from "../../types/room";
import { Card } from "../ui/Card";
import { formatPrice } from "../../lib/currency";
import { formatDisplayDate, nightsBetween } from "../../lib/dates";
import { useT } from "../../i18n/useT";

interface BookingSummaryProps {
  room: Room;
  dateFrom: string;
  dateTo: string;
}

export function BookingSummary({ room, dateFrom, dateTo }: BookingSummaryProps) {
  const t = useT();
  const nights = nightsBetween(dateFrom, dateTo);
  const total = room.price * nights;

  return (
    <Card>
      <h3 className="mb-4 text-xl font-bold text-ink">
        {t.bookingSummary.title}
      </h3>
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-muted">{t.bookingSummary.room}</span>
          <span className="font-medium text-ink">{room.title}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted">{t.bookingSummary.checkIn}</span>
          <span className="text-ink">{formatDisplayDate(dateFrom)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted">{t.bookingSummary.checkOut}</span>
          <span className="text-ink">{formatDisplayDate(dateTo)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted">{t.bookingCard.nights(nights)}</span>
          <span className="text-ink">{nights}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted">{t.bookingSummary.pricePerNight}</span>
          <span className="text-ink">{formatPrice(room.price)}</span>
        </div>
        <div className="border-t border-divider pt-3">
          <div className="flex justify-between">
            <span className="font-semibold text-ink">{t.bookingSummary.total}</span>
            <span className="text-xl font-bold text-brand">
              {formatPrice(total)}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}
