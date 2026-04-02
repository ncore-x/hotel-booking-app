import { useSearchStore } from "../../stores/searchStore";

export function SortControls() {
  const { sortBy, order, setSort } = useSearchStore();

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-gray-500 dark:text-gray-400">Сортировка:</span>
      <select
        value={`${sortBy}-${order}`}
        onChange={(e) => {
          const [s, o] = e.target.value.split("-") as [typeof sortBy, typeof order];
          setSort(s, o);
        }}
        className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800"
      >
        <option value="id-asc">По умолчанию</option>
        <option value="title-asc">Название (А-Я)</option>
        <option value="title-desc">Название (Я-А)</option>
        <option value="location-asc">Город (А-Я)</option>
        <option value="location-desc">Город (Я-А)</option>
      </select>
    </div>
  );
}
