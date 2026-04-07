import { get, post, del } from "./client";
import type { Facility } from "../types/facility";
import type { PaginatedResponse } from "../types/pagination";

import { buildQuery } from "../lib/queryString";

export const facilitiesApi = {
  getAll: (params?: { page?: number; per_page?: number }) =>
    get<PaginatedResponse<Facility>>(`/facilities${buildQuery(params ?? {})}`),

  create: (title: string) => post<Facility>("/facilities", { title }),

  delete: (id: number) => del(`/facilities/${id}`),
};
