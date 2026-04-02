import { Link } from "react-router";
import { Button } from "../components/ui/Button";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <h1 className="text-6xl font-bold text-gray-300 dark:text-gray-600">404</h1>
      <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
        Страница не найдена
      </p>
      <Link to="/" className="mt-6">
        <Button>На главную</Button>
      </Link>
    </div>
  );
}
