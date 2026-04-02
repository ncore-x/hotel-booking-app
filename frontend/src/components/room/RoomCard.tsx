import type { Room } from "../../types/room";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { FacilityBadge } from "./FacilityBadge";
import { formatPrice } from "../../lib/currency";

interface RoomCardProps {
  room: Room;
  onBook: (roomId: number) => void;
}

export function RoomCard({ room, onBook }: RoomCardProps) {
  return (
    <Card>
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div className="flex-1 space-y-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {room.title}
          </h3>
          {room.description && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {room.description}
            </p>
          )}
          {room.facilities.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {room.facilities.map((f) => (
                <FacilityBadge key={f.id} facility={f} />
              ))}
            </div>
          )}
          <p className="text-xs text-gray-400 dark:text-gray-500">
            {room.quantity} {room.quantity === 1 ? "номер" : "номеров"} всего
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {formatPrice(room.price)}
            <span className="text-sm font-normal text-gray-500"> / ночь</span>
          </p>
          <Button size="sm" onClick={() => onBook(room.id)}>
            Забронировать
          </Button>
        </div>
      </div>
    </Card>
  );
}
