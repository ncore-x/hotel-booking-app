import { format, addDays } from "date-fns";

export function formatDate(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return format(d, "yyyy-MM-dd");
}

export function formatDisplayDate(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date + "T00:00:00") : date;
  return format(d, "dd.MM.yyyy");
}

export function getDefaultDateFrom(): string {
  return formatDate(new Date());
}

export function getDefaultDateTo(): string {
  return formatDate(addDays(new Date(), 14));
}

export function nightsBetween(from: string, to: string): number {
  const ms = new Date(to).getTime() - new Date(from).getTime();
  return Math.max(0, Math.round(ms / (1000 * 60 * 60 * 24)));
}
