import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { authApi } from "../api/auth";
import { useAuthStore } from "../stores/authStore";
import { ApiError } from "../api/client";
import { Spinner } from "../components/ui/Spinner";
import { useT } from "../i18n/useT";

export function OAuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { fetchMe } = useAuthStore();
  const t = useT();
  const cb = t.oauthCallback;

  const [error, setError] = useState<string | null>(null);
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const provider = sessionStorage.getItem("oauth_provider");

    if (!code || !state || !provider) {
      setError(cb.error);
      return;
    }

    sessionStorage.removeItem("oauth_provider");

    (async () => {
      try {
        await authApi.oauthCallback(provider, code, state);
        await fetchMe();
        navigate("/", { replace: true });
      } catch (e) {
        if (e instanceof ApiError && e.status === 409) {
          setError(cb.conflict);
        } else {
          setError(cb.error);
        }
      }
    })();
  }, []);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface px-4">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
            <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <p className="text-base font-semibold text-ink">{error}</p>
          <button
            onClick={() => navigate("/login", { replace: true })}
            className="rounded-xl bg-brand px-6 py-2.5 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv"
          >
            {t.login.submit}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface">
      <div className="flex flex-col items-center gap-4">
        <Spinner size="lg" />
        <p className="text-sm text-muted">{cb.loading}</p>
      </div>
    </div>
  );
}
