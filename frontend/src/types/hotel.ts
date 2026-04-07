export interface Hotel {
  id: number;
  title: string;
  city: string;
  address: string | null;
  cover_image_url?: string | null;
}

export interface HotelSuggestion {
  title: string;
  city: string;
  address?: string | null;
}

export interface AutocompleteResult {
  locations: string[];
  hotels: HotelSuggestion[];
}

export interface HotelAddRequest {
  title: string;
  city: string;
  address?: string;
}

export type HotelSortBy = "id" | "title" | "city";
export type SortOrder = "asc" | "desc";

export interface HotelSearchParams {
  date_from?: string;
  date_to?: string;
  city?: string;
  title?: string;
  search?: string;
  guests?: number;
  page?: number;
  per_page?: number;
  sort_by?: HotelSortBy;
  order?: SortOrder;
}
