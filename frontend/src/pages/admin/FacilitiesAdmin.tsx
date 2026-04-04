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
      setError(
        e instanceof ApiError ? e.detail : "Ошибка добавления"
      );
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 px-8 py-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black uppercase tracking-tight text-ink">
          Удобства
        </h1>
        <p className="mt-1 text-sm text-muted">
          Управление список доступных удобств для номеров
        </p>
      </div>

      {/* Add Form */}
      <div className="flex gap-3">
        <div className="flex-1">
          <Input
            placeholder="Названием нового удобства (e.g. Wi-Fi, Кондиционер)"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
        </div>
        <Button
          loading={adding}
          onClick={handleAdd}
          className="bg-brand text-on-brand hover:bg-brand-hv shrink-0 flex items-center gap-2"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Добавить
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="rounded-lg border border-fail/20 bg-fail/5 p-4 text-fail">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <p className="font-medium">Ошибка</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : facilities.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-divider bg-secondary/30 py-16">
          <svg
            className="h-12 w-12 text-subtle mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-ink mb-1">
            Нет удобств
          </h3>
          <p className="text-muted text-sm">
            Добавьте первое удобство, чтобы начать работу
          </p>
        </div>
      ) : (
        <Card className="p-6">
          <div className="flex flex-wrap gap-2">
            {facilities.map((f) => (
              <div
                key={f.id}
                className="inline-flex items-center rounded-full bg-secondary text-muted px-3 py-1.5 text-sm font-medium hover:bg-secondary/80 transition-colors group"
              >
                <svg
                  className="h-4 w-4 mr-2 text-subtle"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                {f.title}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
