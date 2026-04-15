import { get, post, patch, del, upload } from "./client";
import type { User, LoginRequest, LoginResponse, UserPasswordUpdate, UserEmailUpdate, UserProfileUpdate } from "../types/user";

export const authApi = {
  register: (data: LoginRequest) => post<User>("/auth/register", data),
  login: (data: LoginRequest) => post<LoginResponse>("/auth/login", data),
  logout: () => post<void>("/auth/logout"),
  getMe: () => get<User>("/auth/me"),
  refresh: () => post<LoginResponse>("/auth/refresh"),
  updatePassword: (data: UserPasswordUpdate) => patch<void>("/auth/me", data),
  updateEmail: (data: UserEmailUpdate) => patch<void>("/auth/me/email", data),
  updateProfile: (data: UserProfileUpdate) => patch<User>("/auth/me/profile", data),
  uploadAvatar: (file: File) => upload<User>("/auth/me/avatar", file),
  deleteAvatar: () => del<void>("/auth/me/avatar"),
  confirmChange: (token: string) => get<{ detail: string }>(`/auth/confirm?token=${encodeURIComponent(token)}`),
  getOAuthUrl: (provider: string) => get<{ url: string }>(`/auth/oauth/${provider}/authorize`),
  oauthCallback: (provider: string, code: string, state: string) =>
    post<LoginResponse>(`/auth/oauth/${provider}/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`),
};
