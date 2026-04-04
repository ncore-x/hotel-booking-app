import { useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { useAuthStore } from "../../stores/authStore";
import { cn } from "../../lib/cn";

const links = [
  {
    to: "/admin/hotels",
    label: "Отели",
    icon: (
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
          d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"
        />
      </svg>
    ),
  },
  {
    to: "/admin/facilities",
    label: "Удобства",
    icon: (
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
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
    ),
  },
];

export function AdminLayout() {
  const user = useAuthStore((s) => s.user);
  const isLoading = useAuthStore((s) => s.isLoading);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && (!user || !user.is_admin)) {
      navigate("/");
    }
  }, [user, isLoading, navigate]);

  if (isLoading || !user?.is_admin) return null;

  return (
    <div className="flex min-h-screen gap-0">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r border-divider bg-card">
        <div className="sticky top-0 h-screen overflow-y-auto">
          {/* Header */}
          <div className="border-b border-divider px-6 py-8">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10">
                <svg
                  className="h-6 w-6 text-brand"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold text-ink">Admin Panel</h1>
                <p className="text-xs text-muted">Управление</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="space-y-1 px-3 py-4">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-brand/10 text-brand font-semibold shadow-sm"
                      : "text-muted hover:bg-secondary hover:text-ink",
                  )
                }
              >
                {link.icon}
                <span>{link.label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Footer */}
          <div className="border-t border-divider px-4 py-4">
            <div className="rounded-lg bg-secondary p-3 text-xs text-subtle">
              <p className="font-medium text-ink mb-1">Совет</p>
              <p>Используй админ-панель для управления отелями, номерами и услугами.</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-surface">
        <div className="min-h-screen">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
