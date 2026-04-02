import { get, post, patch, del } from "./client";
import type { Booking, BookingAddRequest, BookingPatchRequest } from "../types/booking";
import type { PaginatedResponse } from "../types/pagination";

import { buildQuery } from "../lib/queryString";

export const bookingsApi = {
  getMy: (params?: { page?: number; per_page?: number }) =>
    get<PaginatedResponse<Booking>>(`/bookings/me${buildQuery(params ?? {})}`),

  getById: (id: number) => get<Booking>(`/bookings/${id}`),

  create: (data: BookingAddRequest) => post<Booking>("/bookings", data),

  patch: (id: number, data: BookingPatchRequest) =>
    patch<Booking>(`/bookings/${id}`, data),

  cancel: (id: number) => del(`/bookings/${id}`),
};
