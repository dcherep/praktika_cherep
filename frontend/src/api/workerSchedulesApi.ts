import api from './axiosInstance';

export interface WorkerSchedule {
  id: number;
  worker_id: number;
  date: string;
  shift_type: string;
  hours: number;
  is_working: boolean;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkerScheduleCreate {
  worker_id: number;
  date: string;
  shift_type: string;
  hours: number;
  is_working: boolean;
  comment?: string;
}

export const workerSchedulesApi = {
  getByWorker: (workerId: number) =>
    api.get(`/worker-schedules/worker/${workerId}/`),

  create: (data: WorkerScheduleCreate) =>
    api.post('/worker-schedules/', data),

  update: (id: number, data: Partial<WorkerScheduleCreate>) =>
    api.patch(`/worker-schedules/${id}/`, data),

  delete: (id: number) =>
    api.delete(`/worker-schedules/${id}/`),
};
