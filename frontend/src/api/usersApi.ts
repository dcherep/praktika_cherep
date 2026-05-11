import api from './axiosInstance';

export interface UserCreate {
  first_name: string;
  last_name: string;
  middle_name?: string;
  email: string;
  phone?: string;
  password: string;
  role_id: number;
  // ID мастерских; для админа может быть пустым.
  workshop_ids?: number[];
}

export interface UserUpdate {
  first_name?: string;
  last_name?: string;
  middle_name?: string;
  email?: string;
  phone?: string;
  password?: string;
  role_id?: number;
  workshop_ids?: number[] | null;
  is_active?: boolean;
}

export const usersApi = {
  list: (params?: { role?: string }) => api.get('/users/', { params }),
  create: (data: UserCreate) => api.post('/users/', data),
  update: (id: number, data: UserUpdate) => api.patch(`/users/${id}`, data),
  deactivate: (id: number) => api.delete(`/users/${id}`),
};
