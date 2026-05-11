import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type UserRole = 'client' | 'master' | 'admin';

interface User {
  id: number;
  name: string;
  role: UserRole;
}

interface AuthStore {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => {
        localStorage.setItem('token', token);
        set({ token, user });
      },
      logout: () => {
        localStorage.removeItem('token');
        set({ token: null, user: null });
      },
    }),
    { name: 'auth-storage', partialize: (s) => ({ token: s.token, user: s.user }) }
  )
);

// Временно для тестирования — КЛИЕНТ
const testUser = {
  id: 1,
  name: "Тестовый Клиент",
  role: "client" as UserRole
};

// Устанавливаем тестовые данные
if (!localStorage.getItem('token')) {
  localStorage.setItem('token', 'test-token');
  useAuthStore.getState().setAuth('test-token', testUser);
}