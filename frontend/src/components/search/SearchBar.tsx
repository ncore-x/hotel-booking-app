import { useSearchStore } from "../../stores/searchStore";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";

interface SearchBarProps {
  onSearch: () => void;
}

export function SearchBar({ onSearch }: SearchBarProps) {
  const { dateFrom, dateTo, location, title, setDates, setLocation, setTitle } =
    useSearchStore();

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Input
          label="Город"
          placeholder="Москва"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <Input
          label="Название"
          placeholder="Grand Hotel"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <Input
          label="Заезд"
          type="date"
          value={dateFrom}
          onChange={(e) => setDates(e.target.value, dateTo)}
        />
        <Input
          label="Выезд"
          type="date"
          value={dateTo}
          min={dateFrom}
          onChange={(e) => setDates(dateFrom, e.target.value)}
        />
        <div className="flex items-end">
          <Button className="w-full" onClick={onSearch}>
            Найти
          </Button>
        </div>
      </div>
    </div>
  );
}
