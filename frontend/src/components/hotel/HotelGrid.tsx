import type { Hotel } from "../../types/hotel";
import { HotelCard } from "./HotelCard";

export function HotelGrid({ hotels }: { hotels: Hotel[] }) {
  if (hotels.length === 0) {
    return (
      <div className="py-16 text-center text-gray-500 dark:text-gray-400">
        <p className="text-lg">Отели не найдены</p>
        <p className="mt-1 text-sm">Попробуйте изменить параметры поиска</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {hotels.map((hotel) => (
        <HotelCard key={hotel.id} hotel={hotel} />
      ))}
    </div>
  );
}
