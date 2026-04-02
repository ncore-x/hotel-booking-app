import { Button } from "./ui/Button";

interface PaginationProps {
  page: number;
  pages: number;
  hasNext: boolean;
  hasPrev: boolean;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pages, hasNext, hasPrev, onPageChange }: PaginationProps) {
  if (pages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-2 pt-6">
      <Button
        variant="secondary"
        size="sm"
        disabled={!hasPrev}
        onClick={() => onPageChange(page - 1)}
      >
        Назад
      </Button>
      <span className="px-3 text-sm text-gray-600 dark:text-gray-400">
        {page} / {pages}
      </span>
      <Button
        variant="secondary"
        size="sm"
        disabled={!hasNext}
        onClick={() => onPageChange(page + 1)}
      >
        Далее
      </Button>
    </div>
  );
}
