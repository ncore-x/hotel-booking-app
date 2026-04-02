import { useState, useEffect, useCallback } from "react";
import { facilitiesApi } from "../../api/facilities";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Card } from "../../components/ui/Card";
import { Spinner } from "../../components/ui/Spinner";
import { ApiError } from "../../api/client";
import type { Facility } from "../../types/facility";

export function FacilitiesAdmin() {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [adding, setAdding] = useState(false);

  const fetchFacilities = useCallback(async () => {
    setLoading(true);
    try {
      const res = await facilitiesApi.getAll({ per_page: 100 });
      setFacilities(res.items);
    } catch {
      setError("Не удалось загрузить удобства");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFacilities();
  }, [fetchFacilities]);

  const handleAdd = async () => {
    if (!newTitle.trim()) return;
    setAdding(true);
    setError(null);
    try {
      await facilitiesApi.create(newTitle.trim());
      setNewTitle("");
      await fetchFacilities();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Ошибка добавления");
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Удобства</h2>

      <div className="flex gap-3">
        <Input
          placeholder="Название удобства"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
        />
        <Button loading={adding} onClick={handleAdd}>
          Добавить
        </Button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      ) : (
        <Card>
          <div className="flex flex-wrap gap-2">
            {facilities.map((f) => (
              <span
                key={f.id}
                className="inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
              >
                {f.title}
              </span>
            ))}
            {facilities.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400">Удобства не добавлены</p>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
