import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { useAuthStore } from "../stores/authStore";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";

export function LoginPage() {
  const { error, clearError, login } = useAuthStore();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch {
      // handled by store
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md pt-12">
      <Card>
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-900 dark:text-white">
          Вход
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              clearError();
            }}
            required
          />
          <Input
            label="Пароль"
            type="password"
            placeholder="********"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              clearError();
            }}
            required
          />

          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}

          <Button className="w-full" loading={loading}>
            Войти
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
          Нет аккаунта?{" "}
          <Link to="/register" className="text-blue-600 hover:underline dark:text-blue-400">
            Зарегистрироваться
          </Link>
        </p>
      </Card>
    </div>
  );
}
