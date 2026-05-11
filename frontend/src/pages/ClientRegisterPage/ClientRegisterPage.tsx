import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '../../api/authApi';
import { workshopsApi, Workshop } from '../../api/workshopsApi';
import { useAuthStore } from '../../store/authStore';

const schema = yup.object({
  first_name: yup.string().required('Обязательное поле'),
  last_name: yup.string().required('Обязательное поле'),
  email: yup.string().email('Неверный формат email').required('Обязательное поле'),
  phone: yup.string().optional(),
  workshop_id: yup
    .mixed<number>()
    .required('Выберите автосервис')
    .test('valid', 'Выберите автосервис', (v) => v !== '' && v !== undefined && !isNaN(Number(v))),
  password: yup.string().min(6, 'Минимум 6 символов').required('Обязательное поле'),
  password_confirm: yup
    .string()
    .oneOf([yup.ref('password')], 'Пароли должны совпадать')
    .required('Обязательное поле'),
});

type FormData = yup.InferType<typeof schema>;

export default function ClientRegisterPage() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [workshops, setWorkshops] = useState<Workshop[]>([]);
  const [workshopsLoading, setWorkshopsLoading] = useState(true);
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: yupResolver(schema) });

  useEffect(() => {
    workshopsApi
      .listPublic()
      .then((res) => setWorkshops(res.data))
      .catch(() => setWorkshops([]))
      .finally(() => setWorkshopsLoading(false));
  }, []);

  const onSubmit = async (data: FormData) => {
    setError('');
    setLoading(true);
    try {
      const res = await authApi.registerClient({
        first_name: data.first_name,
        last_name: data.last_name,
        email: data.email,
        phone: data.phone,
        password: data.password,
        workshop_id: Number(data.workshop_id),
      });
      const { token, user } = res.data;
      setAuth(token, { id: user.id, name: user.name, role: user.role as any });
      navigate('/app/orders');
    } catch (e: any) {
      const msg =
        e?.response?.data?.detail === 'Email уже занят'
          ? 'Пользователь с таким email уже существует'
          : 'Не удалось завершить регистрацию';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-dark to-primary">
      <div className="w-full max-w-md mx-4">
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">🔧</div>
          <h1 className="text-3xl font-bold text-white">Автосервис</h1>
          <p className="text-blue-200 mt-1 text-sm">Регистрация клиента</p>
        </div>
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-bold text-primary-dark mb-6 text-center">
            Создание клиентского аккаунта
          </h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Имя</label>
                <input
                  type="text"
                  {...register('first_name')}
                  className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
                {errors.first_name && (
                  <p className="text-danger text-xs mt-1">{errors.first_name.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Фамилия</label>
                <input
                  type="text"
                  {...register('last_name')}
                  className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
                {errors.last_name && (
                  <p className="text-danger text-xs mt-1">{errors.last_name.message}</p>
                )}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                placeholder="client@mail.ru"
                {...register('email')}
                className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm"
              />
              {errors.email && <p className="text-danger text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Телефон</label>
              <input
                type="tel"
                placeholder="+7..."
                {...register('phone')}
                className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm"
              />
              {errors.phone && <p className="text-danger text-xs mt-1">{errors.phone.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Автосервис (город)
              </label>
              <select
                {...register('workshop_id')}
                className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                disabled={workshopsLoading}
              >
                <option value="">Выберите автосервис...</option>
                {workshops.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.city} — {w.name}
                  </option>
                ))}
              </select>
              {errors.workshop_id && (
                <p className="text-danger text-xs mt-1">{errors.workshop_id.message}</p>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
                <input
                  type="password"
                  {...register('password')}
                  className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
                {errors.password && (
                  <p className="text-danger text-xs mt-1">{errors.password.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Подтверждение пароля
                </label>
                <input
                  type="password"
                  {...register('password_confirm')}
                  className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                />
                {errors.password_confirm && (
                  <p className="text-danger text-xs mt-1">{errors.password_confirm.message}</p>
                )}
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 text-danger rounded-xl text-sm flex items-center gap-2">
                <span>⚠</span> {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary text-white rounded-xl hover:bg-primary-dark disabled:opacity-50 transition font-semibold text-sm"
            >
              {loading ? 'Регистрация...' : 'Зарегистрироваться'}
            </button>
          </form>

          <p className="text-xs text-gray-400 text-center mt-6">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="text-primary hover:text-primary-dark underline">
              Войти
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

