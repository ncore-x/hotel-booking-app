import { create } from "zustand";
import { persist } from "zustand/middleware";

export type NotificationType =
  | "booking_created"
  | "booking_cancelled"
  | "booking_updated"
  | "password_sent"
  | "email_sent";

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  timestamp: number;
  read: boolean;
}

interface NotificationState {
  notifications: AppNotification[];
  add: (type: NotificationType, title: string, body: string) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  clear: () => void;
}

export const useNotificationStore = create<NotificationState>()(
  persist(
    (set) => ({
      notifications: [],

      add: (type, title, body) =>
        set((s) => {
          const next: AppNotification = {
            id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
            type,
            title,
            body,
            timestamp: Date.now(),
            read: false,
          };
          // Keep the 30 most recent notifications
          return { notifications: [next, ...s.notifications].slice(0, 30) };
        }),

      markRead: (id) =>
        set((s) => ({
          notifications: s.notifications.map((n) =>
            n.id === id ? { ...n, read: true } : n,
          ),
        })),

      markAllRead: () =>
        set((s) => ({
          notifications: s.notifications.map((n) => ({ ...n, read: true })),
        })),

      clear: () => set({ notifications: [] }),
    }),
    { name: "notifications" },
  ),
);
