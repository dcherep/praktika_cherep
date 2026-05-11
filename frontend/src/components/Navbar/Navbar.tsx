import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

const ROLE_LABELS: Record<string,string> = { client:'Клиент', master:'Мастер смены', admin:'Администратор' };
const ROLE_BADGE: Record<string,string> = { client:'bg-gray-200 text-gray-700', master:'bg-blue-200 text-blue-800', admin:'bg-purple-200 text-purple-800' };

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-lg text-sm font-medium transition ${isActive ? 'bg-white/20 text-white' : 'text-blue-100 hover:text-white hover:bg-white/10'}`;

  return (
    <nav className="bg-primary-dark text-white px-6 py-3 flex items-center justify-between shadow-md">
      <div className="flex items-center gap-1">
        <NavLink to="/app/orders" className="flex items-center gap-2 mr-4 font-bold text-white text-lg">
          <span>🔧</span> Автосервис
        </NavLink>
        <NavLink to="/app/orders" className={linkClass}>Заявки</NavLink>
        {(user?.role === 'client' || user?.role === 'admin') && (
          <NavLink to="/app/services" className={linkClass}>Услуги</NavLink>
        )}
        {(user?.role === 'master' || user?.role === 'admin') && (
          <NavLink to="/app/workers" className={linkClass}>Работники</NavLink>
        )}
        {user?.role === 'admin' && (
          <NavLink to="/app/users" className={linkClass}>Пользователи</NavLink>
        )}
      </div>
      <div className="flex items-center gap-3">
        {user && (
          <>
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium">{user.name}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ROLE_BADGE[user.role]||'bg-gray-200'}`}>
                {ROLE_LABELS[user.role]||user.role}
              </span>
            </div>
            <button onClick={handleLogout}
              className="px-3 py-2 rounded-lg border border-white/30 text-sm hover:bg-white/10 transition">
              Выйти
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
