import type { Facility } from "./facility";

export interface Room {
  id: number;
  hotel_id: number;
  title: string;
  description: string | null;
  price: number;
  quantity: number;
  capacity: number;
  facilities: Facility[];
}

export interface RoomAddRequest {
  title: string;
  description?: string;
  price: number;
  quantity: number;
  capacity: number;
  facilities_ids: number[];
}
