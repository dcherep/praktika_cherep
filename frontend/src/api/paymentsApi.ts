import api from './axiosInstance';
export const paymentsApi = {
  stub: (data: { order_id: number; amount: number; card_number?: string }) =>
    api.post('/payments/stub', data),
};
