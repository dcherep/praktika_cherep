import api from './axiosInstance';

export const ordersApi = {
  list: (params?: Record<string, string | number>) =>
    api.get('/orders/', { params }),
  listMy: () => api.get('/orders/my'),
  get: (id: number) => api.get(`/orders/${id}`),
  create: (data: object) => api.post('/orders/', data),
  update: (id: number, data: object) => api.patch(`/orders/${id}`, data),
  delete: (id: number) => api.delete(`/orders/${id}`),
  getWorkers: (orderId: number) =>
    api.get(`/orders/${orderId}/workers`),
  assignWorker: (orderId: number, workerId: number) =>
    api.post(`/orders/${orderId}/workers`, null, { params: { worker_id: workerId } }),
};