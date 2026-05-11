import api from './axiosInstance';

export interface Worker {
  id: number;
  first_name: string;
  last_name: string;
  position?: string | null;
  workshop_id: number;
  is_active: boolean;
  is_assigned: boolean;
}

export interface WorkerCreate {
  first_name: string;
  last_name: string;
  position?: string;
  workshop_id?: number | null;
}

export interface WorkerUpdate {
  first_name?: string;
  last_name?: string;
  position?: string;
  is_active?: boolean;
}

export const workersApi = {
  list: () => api.get<Worker[]>('/workers/'),
  listByWorkshop: (workshopId: number) => api.get<Worker[]>(`/workers/workshop/${workshopId}`),
  create: (data: WorkerCreate) => api.post<Worker>('/workers/', data),
  update: (id: number, data: WorkerUpdate) => api.patch<Worker>(`/workers/${id}`, data),
};

