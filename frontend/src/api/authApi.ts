import api from './axiosInstance';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: { id: number; name: string; role: string };
  token_type: string;
}

export interface ClientRegisterRequest {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  password: string;
  workshop_id: number;
}

export const authApi = {
  login: (data: LoginRequest) => api.post<LoginResponse>('/auth/login', data),
  registerClient: (data: ClientRegisterRequest) =>
    api.post<LoginResponse>('/auth/register/client', data),
};
