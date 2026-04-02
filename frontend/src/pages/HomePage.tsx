import { useState, useCallback, useEffect } from "react";
import { SearchBar } from "../components/search/SearchBar";
import { SortControls } from "../components/search/SortControls";
import { HotelGrid } from "../components/hotel/HotelGrid";
import { Pagination } from "../components/Pagination";
import { Spinner } from "../components/ui/Spinner";
import { useSearchStore } from "../stores/searchStore";
import { useDebounce } from "../hooks/useDebounce";
import { hotelsApi } from "../api/hotels";
import type { Hotel } from "../types/hotel";

export function HomePage() {
  const { dateFrom, dateTo, sortBy, order, page, perPage, setPage } =
    useSearchStore();
  const rawLocation = useSearchStore((s) => s.location);
  const rawTitle = useSearchStore((s) => s.title);
  const location = useDebounce(rawLocation, 400);
  const title = useDebounce(rawTitle, 400);

  const [result, setResult] = useState<{
    items: Hotel[];
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  }>({ items: [], pages: 1, has_next: false, has_prev: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await hotelsApi.search({
        date_from: dateFrom,
        date_to: dateTo,
        location: location || undefined,
        title: title || undefined,
        sort_by: sortBy,
        order,
        page,
        per_page: perPage,
      });
      setResult({
        items: res.items,
        pages: res.pages,
        has_next: res.has_next,
        has_prev: res.has_prev,
      });
    } catch {
      setError("Не удалось загрузить отели");
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, location, title, sortBy, order, page, perPage]);

  useEffect(() => {
    search();
  }, [search]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
          Поиск отелей
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Найдите идеальный отель для вашего путешествия
        </p>
      </div>

      <SearchBar onSearch={search} />
      <SortControls />

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : error ? (
        <div className="py-16 text-center text-red-500">{error}</div>
      ) : (
        <>
          <HotelGrid hotels={result.items} />
          <Pagination
            page={page}
            pages={result.pages}
            hasNext={result.has_next}
            hasPrev={result.has_prev}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
