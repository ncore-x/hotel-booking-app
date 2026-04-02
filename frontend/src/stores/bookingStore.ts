import { create } from "zustand";

interface BookingState {
  dateFrom: string;
  dateTo: string;
  roomId: number | null;
  hotelId: number | null;

  setDates: (from: string, to: string) => void;
  setRoom: (hotelId: number, roomId: number) => void;
  reset: () => void;
}

export const useBookingStore = create<BookingState>((set) => ({
  dateFrom: "",
  dateTo: "",
  roomId: null,
  hotelId: null,

  setDates: (dateFrom, dateTo) => set({ dateFrom, dateTo }),
  setRoom: (hotelId, roomId) => set({ hotelId, roomId }),
  reset: () => set({ dateFrom: "", dateTo: "", roomId: null, hotelId: null }),
}));
