/**
 * Главный компонент приложения. Роутинг (React Router v6).
 *
 * ============================================================================
 * ЗОНА РАБОТЫ ИСЛАМА
 * ============================================================================
 *
 * ИСЛАМ, ТУТ: Здесь настраивается роутинг и защищённые маршруты.
 *
 * 1. ЗАЩИТА ОТ НЕАВТОРИЗОВАННЫХ:
 *    - UseProtectedRoute: проверяет токен в localStorage.
 *    - Если нет токена → редирект на /login.
 *    - Оберни защищённые маршруты в <Route element={<ProtectedRoute />}>.
 *
 * 2. ПРОВЕРКА РОЛИ:
 *    - UseRoleRoute: проверяет role пользователя (admin, master, client).
 *    - Только Admin видит /users и /reports.
 *    - Master + Admin видят /reports/personal.
 *    - Navbar скрывает пункты по role (см. TZ раздел 6.2).
 *
 * 3. СТРАНИЦЫ ИЗ РАЗДЕЛА 6 ТЗ — ГДЕ ВЕРСТАТЬ:
 *    - /login         → LoginPage       (форма: email, пароль, валидация Yup)
 *    - /orders        → OrdersPage      (таблица с фильтрами, Badge статусов)
 *    - /orders/new    → CreateOrderPage (форма: ФИО, авто, услуги → далее на /payment)
 *    - /payment       → PaymentPage     (заглушка: карта, итого, кнопка «Оплатить»)
 *    - /services      → ServicesPage   (клиент: readonly, admin: редактирование)
 *    - /users         → UsersPage      (только Admin: таблица, CRUD)
 *    - /reports       → ReportsPage    (Master/Admin: отчёты)
 *
 * 4. ДИЗАЙН (раздел 7 ТЗ):
 *    - Цвета: primary #2E75B6, primary-dark #1F3864.
 *    - Badge статусов: new=серый, in_progress=синий, in_repair=оранжевый, done=зелёный.
 *    - border-radius: 8px, адаптивность 360–1920px.
 * ============================================================================
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import LandingPage from './pages/LandingPage/LandingPage';
import LoginPage from './pages/LoginPage/LoginPage';
import ClientRegisterPage from './pages/ClientRegisterPage/ClientRegisterPage';
import OrdersPage from './pages/OrdersPage/OrdersPage';
import CreateOrderPage from './pages/CreateOrderPage/CreateOrderPage';
import PaymentPage from './pages/PaymentPage/PaymentPage';
import ServicesPage from './pages/ServicesPage/ServicesPage';
import UsersPage from './pages/UsersPage/UsersPage';
import WorkersPage from './pages/WorkersPage/WorkersPage';
import Layout from './components/Layout/Layout';

function ClientOnlyRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  // Только клиенты могут видеть оплату
  if (user?.role === 'master' || user?.role === 'admin') {
    return <Navigate to="/app/orders" replace />;
  }
  return <>{children}</>;
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function RoleRoute({
  roles,
  children,
}: {
  roles: string[];
  children: React.ReactNode;
}) {
  const user = useAuthStore((s) => s.user);
  if (!user || !roles.includes(user.role)) {
    return <Navigate to="/app/orders" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<LandingPage />}
      />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<ClientRegisterPage />} />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="orders" element={<OrdersPage />} />
        <Route path="orders/new" element={<CreateOrderPage />} />
        <Route path="payment" element={
          <ClientOnlyRoute>
            <PaymentPage />
          </ClientOnlyRoute>
        } />
        <Route path="services" element={<ServicesPage />} />
        <Route
          path="users"
          element={
            <RoleRoute roles={['admin']}>
              <UsersPage />
            </RoleRoute>
          }
        />
        <Route
          path="workers"
          element={
            <RoleRoute roles={['master', 'admin']}>
              <WorkersPage />
            </RoleRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
