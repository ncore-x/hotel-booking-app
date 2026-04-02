import { useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { useAuthStore } from "../../stores/authStore";
import { cn } from "../../lib/cn";

const links = [
  { to: "/admin/hotels", label: "Отели" },
  { to: "/admin/facilities", label: "Удобства" },
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
    <div className="flex gap-8">
      <nav className="w-48 shrink-0 space-y-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              cn(
                "block rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                  : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800",
              )
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="min-w-0 flex-1">
        <Outlet />
      </div>
    </div>
  );
}
