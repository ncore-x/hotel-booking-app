import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { authApi } from "../api/auth";
import { ApiError } from "../api/client";
import { Spinner } from "../components/ui/Spinner";
import { useT } from "../i18n/useT";

export function ConfirmPage() {
  const [searchParams] = useSearchParams();
  const t = useT();
  const p = t.profilePage;

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMsg, setErrorMsg] = useState<string>(p.confirmError);

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setErrorMsg(p.confirmError);
      setStatus("error");
      return;
    }

    let cancelled = false;
    authApi
      .confirmChange(token)
      .then(() => {
        if (!cancelled) setStatus("success");
      })
      .catch((err) => {
        if (!cancelled) {
          setErrorMsg(err instanceof ApiError ? err.detail : p.confirmError);
          setStatus("error");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [searchParams, p.confirmError]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-md rounded-2xl border border-divider bg-card p-10 text-center shadow-sm">
        {status === "loading" && (
          <>
            <div className="mb-6 flex justify-center">
              <Spinner size="lg" />
            </div>
            <p className="text-sm text-muted">{p.confirmLoading}</p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="mb-6 flex justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-brand/10">
                <svg
                  className="h-8 w-8 text-brand"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <h1
              className="mb-2 text-2xl font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {p.confirmSuccess}
            </h1>
            <p className="mb-8 text-sm text-muted">
              Ваши данные обновлены.
            </p>
            <Link
              to="/profile"
              className="inline-block rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv"
            >
              Перейти в профиль
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <div className="mb-6 flex justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-fail/10">
                <svg
                  className="h-8 w-8 text-fail"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            </div>
            <h1
              className="mb-2 text-2xl font-black uppercase tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Ошибка подтверждения
            </h1>
            <p className="mb-8 text-sm text-muted">{errorMsg}</p>
            <Link
              to="/profile"
              className="inline-block rounded-full border border-divider px-6 py-2.5 text-sm font-semibold text-ink transition-colors hover:border-brand hover:text-brand"
            >
              Вернуться в профиль
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
