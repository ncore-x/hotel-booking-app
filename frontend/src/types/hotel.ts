export interface Hotel {
  id: number;
  title: string;
  location: string;
}

export interface HotelAddRequest {
  title: string;
  location: string;
}

export type HotelSortBy = "id" | "title" | "location";
export type SortOrder = "asc" | "desc";

export interface HotelSearchParams {
  date_from: string;
  date_to: string;
  location?: string;
  title?: string;
  page?: number;
  per_page?: number;
  sort_by?: HotelSortBy;
  order?: SortOrder;
}
