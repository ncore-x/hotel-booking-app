export interface Booking {
  id: number;
  user_id: number;
  room_id: number;
  date_from: string;
  date_to: string;
  price: number;
}

export interface BookingAddRequest {
  room_id: number;
  date_from: string;
  date_to: string;
}

export interface BookingPatchRequest {
  date_from?: string;
  date_to?: string;
}
