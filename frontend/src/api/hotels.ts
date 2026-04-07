import { get, post, put, patch, del } from "./client";
import type { Hotel, HotelAddRequest, HotelSearchParams, AutocompleteResult } from "../types/hotel";
import type { PaginatedResponse } from "../types/pagination";
import { buildQuery } from "../lib/queryString";

export const hotelsApi = {
  search: (params: HotelSearchParams) =>
    get<PaginatedResponse<Hotel>>(`/hotels${buildQuery({ ...params })}`),

  getById: (id: number) => get<Hotel>(`/hotels/${id}`),

  create: (data: HotelAddRequest) => post<Hotel>("/hotels", data),

  update: (id: number, data: HotelAddRequest) =>
    put<Hotel>(`/hotels/${id}`, data),

  patch: (id: number, data: Partial<HotelAddRequest>) =>
    patch<Hotel>(`/hotels/${id}`, data),

  delete: (id: number) => del(`/hotels/${id}`),

  autocomplete: (q: string) =>
    get<AutocompleteResult>(`/hotels/autocomplete${buildQuery({ q })}`),

  popularLocations: () =>
    get<string[]>(`/hotels/popular-locations`),
};
