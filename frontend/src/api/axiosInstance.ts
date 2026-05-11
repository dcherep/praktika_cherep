/**
 * Базовый Axios-инстанс с JWT-интерцепторами.
 * 
 * ============================================================================
 * ЗОНА РАБОТЫ ИСЛАМА
 * ============================================================================
 * 
 * ИСЛАМ, ТУТ: Этот инстанс используется для всех API-запросов.
 * 
 * 1. ПРОБРАСЫВАНИЕ ТОКЕНА:
 *    - При каждом запросе интерцептор request добавляет заголовок:
 *      Authorization: Bearer <token>
 *    - Токен берётся из localStorage.getItem('token')
 *    - Убедись, что после логина токен сохраняется: localStorage.setItem('token', token)
 * 
 * 2. ОБРАБОТКА 401:
 *    - При ответе 401 (Unauthorized) интерцептор response:
 *      - Удаляет токен из localStorage
 *      - Редиректит на /login
 *    - Если нужен другой сценарий (например, refresh token) — измени здесь.
 * 
 * 3. BASE URL:
 *    - Используется VITE_API_URL из .env (при сборке) или дефолт http://localhost:8000
 *    - В Docker: задаётся через environment
 * 
 * 4. ИСПОЛЬЗОВАНИЕ:
 *    import api from '@/api/axiosInstance';
 *    const data = await api.get('/orders/');
 * ============================================================================
 */

import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Токен: из localStorage (после логина) или из store (после перезагрузки, rehydrate из auth-storage)
function getToken(): string | null {
  return localStorage.getItem('token') || useAuthStore.getState().token;
}

// Добавляем Bearer-токен к каждому запросу
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// При 401 — выход и редирект на логин
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
