import { create } from "zustand";
import { authApi } from "../api/auth";
import type { User } from "../types/user";
import { ApiError } from "../api/client";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;

  fetchMe: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  error: null,

  fetchMe: async () => {
    try {
      const user = await authApi.getMe();
      set({ user, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },

  login: async (email, password) => {
    set({ error: null });
    try {
      await authApi.login({ email, password });
      const user = await authApi.getMe();
      set({ user });
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : "Ошибка входа";
      set({ error: msg });
      throw e;
    }
  },

  register: async (email, password) => {
    set({ error: null });
    try {
      await authApi.register({ email, password });
      await get().login(email, password);
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : "Ошибка регистрации";
      set({ error: msg });
      throw e;
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } finally {
      set({ user: null });
    }
  },

  clearError: () => {
    if (get().error !== null) set({ error: null });
  },
}));
