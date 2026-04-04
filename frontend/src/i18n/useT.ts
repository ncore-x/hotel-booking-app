import { useLangStore } from "../stores/langStore";
import { translations } from "./translations";

export function useT() {
  const lang = useLangStore((s) => s.lang);
  return translations[lang];
}
