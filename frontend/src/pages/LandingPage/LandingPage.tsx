import { useNavigate } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-dark to-primary">
      <div className="w-full max-w-xl mx-4">
        <div className="bg-white/95 backdrop-blur rounded-3xl shadow-2xl p-8 md:p-10">
          <div className="flex flex-col items-center text-center mb-6">
            <div className="text-5xl mb-3">🔧</div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-primary-dark">Автосервис</h1>
            <p className="text-gray-500 mt-2 text-sm md:text-base">
              Система онлайн-заявок и управления мастерской
            </p>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => navigate('/login')}
              className="w-full py-3.5 rounded-xl bg-primary text-white font-semibold text-sm md:text-base
                         hover:bg-primary-dark transition shadow-md"
            >
              Войти в систему
            </button>
            <button
              onClick={() => navigate('/register')}
              className="w-full py-3.5 rounded-xl border border-primary text-primary font-semibold text-sm md:text-base
                         hover:bg-primary/5 transition"
            >
              Зарегистрироваться как клиент
            </button>
          </div>

          <p className="text-xs text-gray-400 text-center mt-5">
            Регистрация доступна только для роли <span className="font-semibold">Клиент</span>.
            {' '}Учётные записи мастеров и администраторов создаёт администратор системы.
          </p>
        </div>
      </div>
    </div>
  );
}

