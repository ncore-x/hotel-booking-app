import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Lang = "en" | "ru";

interface LangState {
  lang: Lang;
  toggle: () => void;
}

export const useLangStore = create<LangState>()(
  persist(
    (set) => ({
      lang: "en",
      toggle: () => set((s) => ({ lang: s.lang === "en" ? "ru" : "en" })),
    }),
    { name: "lang" },
  ),
);
