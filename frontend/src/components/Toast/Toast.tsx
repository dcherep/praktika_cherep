import { useState, useCallback } from 'react';

type ToastType = 'success' | 'error' | 'info';
interface ToastItem { id: number; message: string; type: ToastType; }

const COLORS = {
  success: 'bg-green-600',
  error: 'bg-danger',
  info: 'bg-primary',
};
const ICONS = { success: '✓', error: '✕', info: 'ℹ' };

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  let nextId = 0;

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = ++nextId;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  const ToastContainer = () => (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div key={t.id}
          className={`${COLORS[t.type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-in min-w-64 max-w-sm pointer-events-auto`}>
          <span className="font-bold text-lg leading-none">{ICONS[t.type]}</span>
          <span className="text-sm">{t.message}</span>
        </div>
      ))}
    </div>
  );

  return { showToast, ToastContainer };
}
