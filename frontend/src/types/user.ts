export interface User {
  id: number;
  email: string;
  is_admin: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserPasswordUpdate {
  current_password: string;
  new_password: string;
}

export interface UserEmailUpdate {
  new_email: string;
  current_password: string;
}
