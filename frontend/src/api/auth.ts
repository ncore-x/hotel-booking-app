import { get, post, patch } from "./client";
import type { User, LoginRequest, LoginResponse, UserPasswordUpdate, UserEmailUpdate } from "../types/user";

export const authApi = {
  register: (data: LoginRequest) => post<User>("/auth/register", data),
  login: (data: LoginRequest) => post<LoginResponse>("/auth/login", data),
  logout: () => post<void>("/auth/logout"),
  getMe: () => get<User>("/auth/me"),
  refresh: () => post<LoginResponse>("/auth/refresh"),
  updatePassword: (data: UserPasswordUpdate) => patch<void>("/auth/me", data),
  updateEmail: (data: UserEmailUpdate) => patch<void>("/auth/me/email", data),
};
