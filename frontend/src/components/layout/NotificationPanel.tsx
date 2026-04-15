import { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNotificationStore } from "../../stores/notificationStore";
import { useLangStore } from "../../stores/langStore";
import { useT } from "../../i18n/useT";
import type { AppNotification, NotificationType } from "../../stores/notificationStore";

// ─── Relative time ────────────────────────────────────────────────────────────

function timeAgo(ts: number, lang: string): string {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 60) return lang === "ru" ? "только что" : "just now";
  const min = Math.floor(diff / 60);
  if (min < 60) return lang === "ru" ? `${min} мин. назад` : `${min}m ago`;
  const h = Math.floor(min / 60);
  if (h < 24) return lang === "ru" ? `${h} ч назад` : `${h}h ago`;
  const d = Math.floor(h / 24);
  return lang === "ru" ? `${d} дн назад` : `${d}d ago`;
}

// ─── Type config ──────────────────────────────────────────────────────────────

const TYPE_STYLES: Record<
  NotificationType,
  { bg: string; text: string; icon: React.ReactNode }
> = {
  booking_created: {
    bg: "bg-green-500/10",
    text: "text-green-600 dark:text-green-400",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  booking_cancelled: {
    bg: "bg-red-500/10",
    text: "text-red-600 dark:text-red-400",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  booking_updated: {
    bg: "bg-blue-500/10",
    text: "text-blue-600 dark:text-blue-400",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5m-9-6h.008v.008H12v-.008zM12 15h.008v.008H12V15zm0 2.25h.008v.008H12v-.008zM9.75 15h.008v.008H9.75V15zm0 2.25h.008v.008H9.75v-.008zM7.5 15h.008v.008H7.5V15zm0 2.25h.008v.008H7.5v-.008zm6.75-4.5h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V15zm0 2.25h.008v.008h-.008v-.008zm2.25-4.5h.008v.008H16.5v-.008zm0 2.25h.008v.008H16.5V15z" />
      </svg>
    ),
  },
  password_sent: {
    bg: "bg-amber-500/10",
    text: "text-amber-600 dark:text-amber-400",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
  },
  email_sent: {
    bg: "bg-purple-500/10",
    text: "text-purple-600 dark:text-purple-400",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
      </svg>
    ),
  },
};

// ─── Notification item ────────────────────────────────────────────────────────

function NotificationItem({
  notification,
  lang,
  onRead,
}: {
  notification: AppNotification;
  lang: string;
  onRead: (id: string) => void;
}) {
  const styles = TYPE_STYLES[notification.type];

  return (
    <button
      onClick={() => onRead(notification.id)}
      className={`w-full border-b border-divider px-4 py-3 text-left transition-colors last:border-0 hover:bg-secondary ${
        notification.read ? "opacity-60" : ""
      }`}
    >
      <div className="flex gap-3">
        {/* Icon */}
        <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${styles.bg} ${styles.text}`}>
          {styles.icon}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="text-xs font-semibold text-ink leading-snug">{notification.title}</p>
            {!notification.read && (
              <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-brand" />
            )}
          </div>
          <p className="mt-0.5 text-xs text-muted leading-snug">{notification.body}</p>
          <p className="mt-1 text-[10px] text-muted/60">{timeAgo(notification.timestamp, lang)}</p>
        </div>
      </div>
    </button>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function NotificationPanel() {
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const { lang } = useLangStore();
  const t = useT();
  const n = t.notifications;

  const { notifications, markRead, markAllRead, clear } = useNotificationStore();
  const unreadCount = notifications.filter((n) => !n.read).length;

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div ref={panelRef} className="relative">
      {/* Bell button */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
        className={`relative flex h-11 w-11 items-center justify-center rounded-full border border-divider text-muted transition-colors hover:border-brand hover:text-brand ${
          open ? "border-brand text-brand" : ""
        }`}
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-brand px-0.5 text-[9px] font-bold text-on-brand leading-none">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-2xl border border-divider bg-card shadow-lg"
          >
            {/* Panel header */}
            <div className="flex items-center justify-between border-b border-divider px-4 py-3">
              <span className="text-xs font-bold uppercase tracking-wider text-ink">
                {n.title}
              </span>
              <div className="flex items-center gap-3">
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    className="text-[11px] font-medium text-brand transition-colors hover:text-brand-hv"
                  >
                    {n.markAllRead}
                  </button>
                )}
                {notifications.length > 0 && (
                  <button
                    onClick={clear}
                    className="text-[11px] font-medium text-muted transition-colors hover:text-ink"
                  >
                    {n.clearAll}
                  </button>
                )}
              </div>
            </div>

            {/* List */}
            {notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 px-4">
                <svg className="mb-3 h-8 w-8 text-muted/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                </svg>
                <p className="text-sm text-muted">{n.empty}</p>
              </div>
            ) : (
              <div className="max-h-96 overflow-y-auto">
                {notifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    lang={lang}
                    onRead={(id) => {
                      markRead(id);
                    }}
                  />
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
