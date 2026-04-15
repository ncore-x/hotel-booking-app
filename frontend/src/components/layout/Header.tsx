import { useState, useEffect } from "react";
import { Link } from "react-router";
import { useAuthStore } from "../../stores/authStore";
import { useThemeStore } from "../../stores/themeStore";
import { useLangStore } from "../../stores/langStore";
import { useT } from "../../i18n/useT";
import { NotificationPanel } from "./NotificationPanel";

export function Header() {
  const { user, logout } = useAuthStore();
  const { theme, toggle } = useThemeStore();
  const { lang, toggle: toggleLang } = useLangStore();
  const t = useT();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-40 bg-card transition-shadow duration-300 ${
        scrolled ? "shadow-sm" : ""
      }`}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-8">
        {/* Logo */}
        <Link
          to="/"
          className="font-display text-xl font-bold tracking-tight text-ink"
          style={{ fontFamily: "var(--font-display)" }}
        >
          StaySpring.
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-8 md:flex">
          <Link to="/" className="text-sm font-medium text-muted transition-colors hover:text-ink">
            {t.nav.home}
          </Link>
          {user?.is_admin && (
            <Link to="/admin/hotels" className="text-sm font-medium text-muted transition-colors hover:text-ink">
              {t.nav.admin}
            </Link>
          )}
        </nav>

        {/* Controls: notifications + lang + theme */}
        <div className="hidden items-center gap-2 md:flex">
          {/* Notifications */}
          {user && <NotificationPanel />}

          {/* Language toggle */}
          <button
            onClick={toggleLang}
            aria-label="Toggle language"
            className="h-11 rounded-full border border-divider px-3 text-xs font-semibold text-muted transition-colors hover:border-brand hover:text-brand"
          >
            {lang === "en" ? "RU" : "EN"}
          </button>

          {/* Theme toggle */}
          <button
            onClick={toggle}
            aria-label="Toggle theme"
            className="flex h-11 w-11 items-center justify-center rounded-full border border-divider text-muted transition-colors hover:border-brand hover:text-brand"
          >
          {theme === "dark" ? (
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m8.66-9h-1M4.34 12h-1m15.07-6.07-.71.71M6.34 17.66l-.71.71m12.73 0-.71-.71M6.34 6.34l-.71-.71M12 7a5 5 0 100 10A5 5 0 0012 7z" />
            </svg>
          ) : (
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0118 15.75 9.75 9.75 0 018.25 6a9.72 9.72 0 01.248-2.252 9.75 9.75 0 1013.255 11.254z" />
            </svg>
          )}
          </button>

          {/* Desktop auth */}
          {user ? (
            <>
              <Link
                to="/bookings"
                className="text-sm font-medium text-muted transition-colors hover:text-ink"
              >
                {t.nav.myBookings}
              </Link>
              <Link
                to="/profile"
                className="flex items-center gap-2.5 transition-opacity hover:opacity-80"
              >
                <div className="h-8 w-8 overflow-hidden rounded-full border border-divider bg-secondary shrink-0">
                  {user.avatar_url ? (
                    <img src={user.avatar_url} alt="avatar" className="h-full w-full object-cover" />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-brand/10">
                      <span className="text-xs font-bold text-brand">
                        {(user.first_name?.[0] ?? user.email[0]).toUpperCase()}
                      </span>
                    </div>
                  )}
                </div>
                <div className="flex flex-col items-start">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-brand leading-none">
                    {t.nav.myProfile}
                  </span>
                  <span className="text-sm font-medium text-muted leading-tight">
                    {user.first_name ?? user.email}
                  </span>
                </div>
              </Link>
              <button
                onClick={logout}
                className="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv"
              >
                {t.nav.signOut}
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm font-medium text-muted transition-colors hover:text-ink"
              >
                {t.nav.logIn}
              </Link>
              <Link
                to="/register"
                className="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv"
              >
                {t.nav.signUp}
              </Link>
            </>
          )}
        </div>

        {/* Mobile: notifications + hamburger */}
        <div className="flex items-center gap-1 md:hidden">
          {user && <NotificationPanel />}
          <button
            className="flex items-center justify-center rounded-lg p-2 text-muted hover:bg-secondary"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Menu"
          >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="border-t border-divider bg-surface px-4 py-4 md:hidden">
          <div className="flex flex-col gap-3">
            <Link to="/" className="text-sm font-medium text-ink" onClick={() => setMenuOpen(false)}>{t.nav.home}</Link>
            <button
              onClick={toggleLang}
              className="flex items-center gap-2 text-sm font-medium text-muted"
            >
              {lang === "en" ? "RU Русский" : "EN English"}
            </button>
            <button
              onClick={toggle}
              className="flex items-center gap-2 text-sm font-medium text-muted"
            >
              {theme === "dark" ? (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m8.66-9h-1M4.34 12h-1m15.07-6.07-.71.71M6.34 17.66l-.71.71m12.73 0-.71-.71M6.34 6.34l-.71-.71M12 7a5 5 0 100 10A5 5 0 0012 7z" />
                  </svg>
                  Light Mode
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0118 15.75 9.75 9.75 0 018.25 6a9.72 9.72 0 01.248-2.252 9.75 9.75 0 1013.255 11.254z" />
                  </svg>
                  Dark Mode
                </>
              )}
            </button>
            {user ? (
              <>
                <Link to="/bookings" className="text-sm font-medium text-ink" onClick={() => setMenuOpen(false)}>{t.nav.myBookings}</Link>
                <Link to="/profile" className="flex flex-col gap-0.5" onClick={() => setMenuOpen(false)}>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-brand">{t.nav.myProfile}</span>
                  <span className="text-sm font-medium text-ink">{user.email}</span>
                </Link>
                {user.is_admin && (
                  <Link to="/admin/hotels" className="text-sm font-medium text-ink" onClick={() => setMenuOpen(false)}>{t.nav.admin}</Link>
                )}
                <button onClick={() => { logout(); setMenuOpen(false); }} className="text-left text-sm font-medium text-muted">{t.nav.signOut}</button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm font-medium text-ink" onClick={() => setMenuOpen(false)}>{t.nav.logIn}</Link>
                <Link to="/register" className="text-sm font-medium text-ink" onClick={() => setMenuOpen(false)}>{t.nav.signUp}</Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
