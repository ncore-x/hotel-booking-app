import type { Room } from "../../types/room";
import { Card } from "../ui/Card";
import { formatPrice } from "../../lib/currency";
import { formatDisplayDate, nightsBetween } from "../../lib/dates";

interface BookingSummaryProps {
  room: Room;
  dateFrom: string;
  dateTo: string;
}

export function BookingSummary({ room, dateFrom, dateTo }: BookingSummaryProps) {
  const nights = nightsBetween(dateFrom, dateTo);
  const total = room.price * nights;

  return (
    <Card>
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Итого
      </h3>
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">Номер</span>
          <span className="font-medium text-gray-900 dark:text-white">{room.title}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">Заезд</span>
          <span className="text-gray-900 dark:text-white">{formatDisplayDate(dateFrom)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">Выезд</span>
          <span className="text-gray-900 dark:text-white">{formatDisplayDate(dateTo)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">Ночей</span>
          <span className="text-gray-900 dark:text-white">{nights}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">Цена за ночь</span>
          <span className="text-gray-900 dark:text-white">{formatPrice(room.price)}</span>
        </div>
        <div className="border-t border-gray-200 pt-3 dark:border-gray-700">
          <div className="flex justify-between">
            <span className="font-semibold text-gray-900 dark:text-white">Итого</span>
            <span className="text-xl font-bold text-blue-600 dark:text-blue-400">
              {formatPrice(total)}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}
