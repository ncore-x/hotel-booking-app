export interface User {
  id: number;
  email: string;
  is_admin: boolean;
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  birth_date?: string | null;
  gender?: string | null;
  citizenship?: string | null;
  avatar_url?: string | null;
  oauth_provider?: string | null;
}

export interface UserProfileUpdate {
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  birth_date?: string | null;
  gender?: string | null;
  citizenship?: string | null;
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
