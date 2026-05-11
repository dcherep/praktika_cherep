import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '../../api/authApi';
import { useAuthStore } from '../../store/authStore';

const schema = yup.object({
  email: yup.string().email('Неверный формат email').required('Обязательное поле'),
  password: yup.string().min(6,'Минимум 6 символов').required('Обязательное поле'),
});
type FormData = yup.InferType<typeof schema>;

export default function LoginPage() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const { register, handleSubmit, formState:{errors} } = useForm<FormData>({ resolver: yupResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError(''); setLoading(true);
    try {
      const res = await authApi.login(data);
      const { token, user } = res.data;
      setAuth(token, { id:user.id, name:user.name, role:user.role as any });
      navigate('/app/orders');
    } catch { setError('Неверный email или пароль'); }
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-dark to-primary">
      <div className="w-full max-w-md mx-4">
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">🔧</div>
          <h1 className="text-3xl font-bold text-white">Автосервис</h1>
          <p className="text-blue-200 mt-1 text-sm">Система управления мастерской</p>
        </div>
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-bold text-primary-dark mb-6 text-center">Вход в систему</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" placeholder="example@mail.ru" {...register('email')}
                className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm" />
              {errors.email && <p className="text-danger text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
              <input type="password" placeholder="••••••••" {...register('password')}
                className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm" />
              {errors.password && <p className="text-danger text-xs mt-1">{errors.password.message}</p>}
            </div>
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 text-danger rounded-xl text-sm flex items-center gap-2">
                <span>⚠</span> {error}
              </div>
            )}
            <button type="submit" disabled={loading}
              className="w-full py-3 bg-primary text-white rounded-xl hover:bg-primary-dark disabled:opacity-50 transition font-semibold text-sm">
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>
          <div className="mt-6 flex flex-col items-center gap-2">
            <p className="text-xs text-gray-400 text-center">
              Нет аккаунта?
            </p>
            <button
              type="button"
              onClick={() => navigate('/register')}
              className="w-full py-2.5 border border-primary text-primary rounded-xl text-sm font-semibold hover:bg-primary/5 transition"
            >
              Зарегистрироваться как клиент
            </button>
            <p className="text-[10px] text-gray-400 text-center mt-1">
              Учётные записи мастеров и администраторов создаёт администратор.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
