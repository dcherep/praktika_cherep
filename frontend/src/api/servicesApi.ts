import api from './axiosInstance';

export const servicesApi = {
  list: () => api.get('/services/'),
  create: (data: { name: string; price?: number }) =>
    api.post('/services/', data),
  update: (id: number, data: { name?: string; price?: number }) =>
    api.patch(`/services/${id}`, data),
};
