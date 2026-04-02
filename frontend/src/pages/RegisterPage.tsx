import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { useAuthStore } from "../stores/authStore";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";

export function RegisterPage() {
  const { error, clearError, register } = useAuthStore();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (password !== confirmPassword) {
      setLocalError("Пароли не совпадают");
      return;
    }
    if (password.length < 6) {
      setLocalError("Пароль должен быть не менее 6 символов");
      return;
    }

    setLoading(true);
    try {
      await register(email, password);
      navigate("/");
    } catch {
      // error is set in store
    } finally {
      setLoading(false);
    }
  };

  const displayError = localError || error;

  return (
    <div className="mx-auto max-w-md pt-12">
      <Card>
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-900 dark:text-white">
          Регистрация
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
              setLocalError(null);
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
              setLocalError(null);
            }}
            required
          />
          <Input
            label="Подтвердите пароль"
            type="password"
            placeholder="********"
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              setLocalError(null);
            }}
            required
          />

          {displayError && (
            <p className="text-sm text-red-500">{displayError}</p>
          )}

          <Button className="w-full" loading={loading}>
            Зарегистрироваться
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
          Уже есть аккаунт?{" "}
          <Link to="/login" className="text-blue-600 hover:underline dark:text-blue-400">
            Войти
          </Link>
        </p>
      </Card>
    </div>
  );
}
