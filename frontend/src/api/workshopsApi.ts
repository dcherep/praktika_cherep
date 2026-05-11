import api from './axiosInstance';

export interface Workshop {
  id: number;
  name: string;
  city: string;
}

export const workshopsApi = {
  /** Список мастерских для админа (требует авторизации) */
  list: () => api.get<Workshop[]>('/workshops/'),
  /** Публичный список мастерских для формы регистрации (без авторизации) */
  listPublic: () => api.get<Workshop[]>('/workshops/public'),
};

