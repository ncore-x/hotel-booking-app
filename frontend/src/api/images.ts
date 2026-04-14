import { get, upload, del } from "./client";
import type { HotelImage } from "../types/image";

export const imagesApi = {
  getByHotel: (hotelId: number) =>
    get<HotelImage[]>(`/hotels/${hotelId}/images`),

  upload: (hotelId: number, file: File) =>
    upload<HotelImage>(`/hotels/${hotelId}/images`, file),

  delete: (hotelId: number, imageId: number) =>
    del(`/hotels/${hotelId}/images/${imageId}`),
};
