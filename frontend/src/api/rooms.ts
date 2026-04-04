import { get, post, put, patch, del } from "./client";
import type { Room, RoomAddRequest } from "../types/room";
import type { PaginatedResponse } from "../types/pagination";
import { buildQuery } from "../lib/queryString";

export const roomsApi = {
  getByHotel: (
    hotelId: number,
    params: { date_from?: string; date_to?: string; page?: number; per_page?: number },
  ) => get<PaginatedResponse<Room>>(`/hotels/${hotelId}/rooms${buildQuery(params)}`),

  getById: (hotelId: number, roomId: number) =>
    get<Room>(`/hotels/${hotelId}/rooms/${roomId}`),

  create: (hotelId: number, data: RoomAddRequest) =>
    post<Room>(`/hotels/${hotelId}/rooms`, data),

  update: (hotelId: number, roomId: number, data: RoomAddRequest) =>
    put<Room>(`/hotels/${hotelId}/rooms/${roomId}`, data),

  patch: (hotelId: number, roomId: number, data: Partial<RoomAddRequest>) =>
    patch<Room>(`/hotels/${hotelId}/rooms/${roomId}`, data),

  delete: (hotelId: number, roomId: number) =>
    del(`/hotels/${hotelId}/rooms/${roomId}`),
};
