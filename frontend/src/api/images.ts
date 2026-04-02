import { get, upload } from "./client";
import type { HotelImage } from "../types/image";

export const imagesApi = {
  getByHotel: (hotelId: number) =>
    get<HotelImage[]>(`/hotels/${hotelId}/images`),

  upload: (hotelId: number, file: File) =>
    upload<HotelImage>(`/hotels/${hotelId}/images`, file),
};
