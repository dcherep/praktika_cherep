/**
 * Layout с Navbar. ИСЛАМ: Navbar читает роль из authStore,
 * условно скрывает пункты меню (Users, Reports — только admin/master).
 */
import { Outlet } from 'react-router-dom';
import Navbar from '../Navbar/Navbar';

export default function Layout() {
  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <Navbar />
      <main className="p-4">
        <Outlet />
      </main>
    </div>
  );
}
