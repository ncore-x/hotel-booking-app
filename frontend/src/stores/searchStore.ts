import { create } from "zustand";
import { getDefaultDateFrom, getDefaultDateTo } from "../lib/dates";
import type { HotelSortBy, SortOrder } from "../types/hotel";

interface SearchState {
  dateFrom: string;
  dateTo: string;
  location: string;
  title: string;
  sortBy: HotelSortBy;
  order: SortOrder;
  page: number;
  perPage: number;

  setDates: (from: string, to: string) => void;
  setLocation: (location: string) => void;
  setTitle: (title: string) => void;
  setSort: (sortBy: HotelSortBy, order: SortOrder) => void;
  setPage: (page: number) => void;
  reset: () => void;
}

const defaults = {
  dateFrom: getDefaultDateFrom(),
  dateTo: getDefaultDateTo(),
  location: "",
  title: "",
  sortBy: "id" as const,
  order: "asc" as const,
  page: 1,
  perPage: 12,
};

export const useSearchStore = create<SearchState>((set) => ({
  ...defaults,

  setDates: (dateFrom, dateTo) => set({ dateFrom, dateTo, page: 1 }),
  setLocation: (location) => set({ location, page: 1 }),
  setTitle: (title) => set({ title, page: 1 }),
  setSort: (sortBy, order) => set({ sortBy, order, page: 1 }),
  setPage: (page) => set({ page }),
  reset: () => set(defaults),
}));
