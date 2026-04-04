import { useSearchStore } from "../../stores/searchStore";
import type { HotelSortBy, SortOrder } from "../../types/hotel";

type SortOption = { sortBy: HotelSortBy; order: SortOrder };

const OPTIONS: Record<string, SortOption> = {
  "id-asc":       { sortBy: "id",       order: "asc"  },
  "title-asc":    { sortBy: "title",    order: "asc"  },
  "title-desc":   { sortBy: "title",    order: "desc" },
  "location-asc": { sortBy: "location", order: "asc"  },
  "location-desc":{ sortBy: "location", order: "desc" },
};

export function SortControls() {
  const { sortBy, order, setSort } = useSearchStore();

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-muted">Сортировка:</span>
      <select
        value={`${sortBy}-${order}`}
        onChange={(e) => {
          const opt = OPTIONS[e.target.value];
          if (opt) setSort(opt.sortBy, opt.order);
        }}
        className="rounded-lg border border-divider bg-card px-3 py-1.5 text-sm text-ink"
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
