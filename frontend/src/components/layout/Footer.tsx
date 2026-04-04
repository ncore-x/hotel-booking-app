import { Link } from "react-router";
import { useT } from "../../i18n/useT";

export function Footer() {
  const t = useT();
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-divider bg-card">
      <div className="mx-auto max-w-7xl px-4 py-10 lg:px-8">
        <div className="flex flex-col gap-8 sm:flex-row sm:justify-between">
          {/* Brand */}
          <div className="space-y-2">
            <p
              className="text-xl font-bold tracking-tight text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              StaySpring.
            </p>
            <p className="max-w-xs text-sm leading-relaxed text-muted">
              {t.footer.tagline}
            </p>
          </div>

          {/* Menu */}
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink">
              {t.footer.menu}
            </p>
            <ul className="space-y-2">
              <li><Link to="/" className="text-sm text-muted transition-colors hover:text-ink">{t.footer.links.home}</Link></li>
              <li><Link to="/bookings" className="text-sm text-muted transition-colors hover:text-ink">{t.nav.myBookings}</Link></li>
              <li><Link to="/profile" className="text-sm text-muted transition-colors hover:text-ink">{t.footer.links.about}</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-divider pt-6">
          <p className="text-center text-xs text-subtle">
            {t.footer.copyright(year)}
          </p>
        </div>
      </div>
    </footer>
  );
}
