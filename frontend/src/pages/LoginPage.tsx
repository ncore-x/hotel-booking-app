import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { useAuthStore } from "../stores/authStore";
import { Input } from "../components/ui/Input";
import { useT } from "../i18n/useT";

const HOTEL_IMG =
  "https://images.unsplash.com/photo-1506059612708-99d6c258160e?w=1200&q=85&auto=format&fit=crop";

export function LoginPage() {
  const { error, clearError, login } = useAuthStore();
  const navigate = useNavigate();
  const t = useT();

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
    <div className="flex min-h-screen">
      {/* Left — photo */}
      <div className="relative hidden w-2/5 flex-shrink-0 lg:block">
        <img src={HOTEL_IMG} alt="Hotel" className="h-full w-full object-cover" />
        <div className="absolute inset-0 bg-black/40" />
        <div className="absolute inset-0 flex flex-col justify-between p-10">
          <Link
            to="/"
            className="text-xl font-black text-white"
            style={{ fontFamily: "var(--font-display)" }}
          >
            StaySpring.
          </Link>
          <p className="text-2xl font-bold leading-snug text-white" style={{ fontFamily: "var(--font-display)" }}>
            {t.home.heroTitle.split("\n").map((line, i) => (
              <span key={i}>{line}{i === 0 && <br />}</span>
            ))}
          </p>
        </div>
      </div>

      {/* Right — form */}
      <div className="flex flex-1 items-center justify-center bg-surface px-6 py-12">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <Link
            to="/"
            className="mb-8 block text-xl font-black text-ink lg:hidden"
            style={{ fontFamily: "var(--font-display)" }}
          >
            StaySpring.
          </Link>

          <h1
            className="mb-1 text-3xl font-black text-ink"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {t.login.title}
          </h1>
          <p className="mb-8 text-sm text-muted">
            {t.login.subtitle}
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label={t.login.email}
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
              label={t.login.password}
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                clearError();
              }}
              required
            />

            {error && <p className="text-sm text-red-500">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center rounded-xl bg-brand py-3 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv disabled:opacity-50"
            >
              {loading ? (
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                t.login.submit
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-muted">
            {t.login.noAccount}{" "}
            <Link to="/register" className="font-semibold text-brand hover:underline">
              {t.login.signUp}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
