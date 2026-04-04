import type { Room } from "../../types/room";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { FacilityBadge } from "./FacilityBadge";
import { formatPrice } from "../../lib/currency";
import { useT } from "../../i18n/useT";

interface RoomCardProps {
  room: Room;
  onBook: (roomId: number) => void;
}

export function RoomCard({ room, onBook }: RoomCardProps) {
  const t = useT();

  return (
    <Card>
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div className="flex-1 space-y-2">
          <h3 className="text-lg font-semibold text-ink">
            {room.title}
          </h3>
          {room.description && (
            <p className="text-sm text-muted">
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
          <p className="text-xs text-subtle">
            {t.roomCard.quantity(room.quantity)}
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <p className="text-2xl font-bold text-ink">
            {formatPrice(room.price)}
            <span className="text-sm font-normal text-muted"> {t.roomCard.perNight}</span>
          </p>
          <Button size="sm" onClick={() => onBook(room.id)}>
            {t.roomCard.book}
          </Button>
        </div>
      </div>
    </Card>
  );
}
