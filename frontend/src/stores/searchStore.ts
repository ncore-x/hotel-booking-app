import { create } from "zustand";
import { getDefaultDateFrom, getDefaultDateTo } from "../lib/dates";
import type { HotelSortBy, SortOrder } from "../types/hotel";

interface SearchState {
  dateFrom: string;
  dateTo: string;
  city: string;
  title: string;
  search: string;
  guests: number;
  sortBy: HotelSortBy;
  order: SortOrder;
  page: number;
  perPage: number;

  setDates: (from: string, to: string) => void;
  setCity: (city: string) => void;
  setTitle: (title: string) => void;
  setSearch: (search: string) => void;
  setGuests: (guests: number) => void;
  setSort: (sortBy: HotelSortBy, order: SortOrder) => void;
  setPage: (page: number) => void;
  reset: () => void;
}

const defaults = {
  dateFrom: getDefaultDateFrom(),
  dateTo: getDefaultDateTo(),
  city: "",
  title: "",
  search: "",
  guests: 2,
  sortBy: "id" as const,
  order: "asc" as const,
  page: 1,
  perPage: 12,
};

export const useSearchStore = create<SearchState>((set) => ({
  ...defaults,

  setDates: (dateFrom, dateTo) => set({ dateFrom, dateTo, page: 1 }),
  setCity: (city) => set({ city, page: 1 }),
  setTitle: (title) => set({ title, page: 1 }),
  setSearch: (search) => set({ search, page: 1 }),
  setGuests: (guests) => set({ guests }),
  setSort: (sortBy, order) => set({ sortBy, order, page: 1 }),
  setPage: (page) => set({ page }),
  reset: () => set(defaults),
}));
