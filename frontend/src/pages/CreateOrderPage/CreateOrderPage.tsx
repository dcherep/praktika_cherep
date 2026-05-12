import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useNavigate } from 'react-router-dom';
import { servicesApi } from '../../api/servicesApi';
import { workshopsApi } from '../../api/workshopsApi';
import { useAuthStore } from '../../store/authStore';
import { ordersApi } from '../../api/ordersApi';
import { useToast } from '../../components/Toast/Toast';
import BookingCalendar from '../../components/BookingCalendar';

const schema = yup.object({
  first_name: yup.string().required('Введите имя'),
  last_name: yup.string().required('Введите фамилию'),
  middle_name: yup.string(),
  phone: yup.string(),
  email: yup.string().email('Неверный формат email'),
  car_brand: yup.string().required('Введите марку'),
  car_model: yup.string().required('Введите модель'),
  car_year: yup.number().typeError('Введите год').min(1900,'Год от 1900').max(new Date().getFullYear(),'Не больше текущего года').required('Введите год'),
  description: yup.string().max(1000),
  service_ids: yup.array().of(yup.number().required()).min(1,'Выберите хотя бы одну услугу').required(),
  workshop_id: yup.number().required('Выберите мастерскую'),
});
type FormData = yup.InferType<typeof schema>;

export default function CreateOrderPage() {
  const [services, setServices] = useState<any[]>([]);
  const [workshops, setWorkshops] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { showToast, ToastContainer } = useToast();
  const [selectedDateTime, setSelectedDateTime] = useState<{ date: string; time: string } | null>(null);

  useEffect(() => { 
    servicesApi.list().then((r) => setServices(r.data));
    workshopsApi.listPublic().then((r) => setWorkshops(r.data));
  }, []);

  const { register, handleSubmit, formState:{errors}, setValue, watch } = useForm<FormData>({
    resolver: yupResolver(schema), defaultValues: { service_ids:[] },
  });
  const handleSelectDateTime = (date: string, time: string) => {
    setSelectedDateTime({ date, time });
  };

  const selectedIds = (watch('service_ids') || []) as number[];
  const total = services.filter((s) => selectedIds.includes(s.id)).reduce((sum, s) => sum + (Number(s.price)||0), 0);

  const onSubmit = async (data: FormData) => {
    setSaving(true);
    try {
      // Мастер создаёт заявку без оплаты — сразу сохраняем
      if (user?.role === 'master' || user?.role === 'admin') {
        await ordersApi.create({
          car_brand: data.car_brand,
          car_model: data.car_model,
          car_year: data.car_year,
          description: data.description || null,
          service_ids: data.service_ids,
          workshop_id: data.workshop_id,
          appointment_date: selectedDateTime?.date,  // добавить дату
          appointment_time: selectedDateTime?.time,  // добавить время
        });
        showToast('Заявка создана!', 'success');
        navigate('/app/orders');
      } else {
        // Клиент идёт на оплату
        const selectedServices = services.filter((s) => data.service_ids?.includes(s.id));
        sessionStorage.setItem('orderDraft', JSON.stringify({ ...data, total, services: selectedServices }));
        navigate('/app/payment');
      }
    } catch {
      showToast('Ошибка при создании заявки', 'error');
    } finally {
      setSaving(false);
    }
  };

  const err = (f: keyof FormData) => errors[f] ? (
    <p className="text-danger text-xs mt-1">{errors[f]?.message as string}</p>
  ) : null;

  const isMaster = user?.role === 'master' || user?.role === 'admin';

 return (
    <div className="max-w-xl mx-auto">
      <ToastContainer />
      <h1 className="text-2xl font-bold text-primary-dark mb-6">
        {isMaster ? 'Новая заявка (от мастера)' : 'Новая заявка'}
      </h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

        {/* Client info */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">Данные клиента</h2>
          <div className="grid grid-cols-1 gap-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Фамилия *</label>
                <input {...register('last_name')} placeholder="Иванов" className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
                {err('last_name')}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Имя *</label>
                <input {...register('first_name')} placeholder="Иван" className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
                {err('first_name')}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Отчество</label>
              <input {...register('middle_name')} placeholder="Иванович" className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Телефон</label>
                <input {...register('phone')} placeholder="+7 999 123-45-67" className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input {...register('email')} type="email" placeholder="ivan@example.ru" className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
                {err('email')}
              </div>
            </div>
          </div>
        </div>

        {/* Workshop selection */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">🏭 Мастерская</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Выберите мастерскую *</label>
            <select {...register('workshop_id', { valueAsNumber: true })}
              className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary bg-white">
              <option value="">-- Выберите мастерскую --</option>
              {workshops.map((ws) => (
                <option key={ws.id} value={ws.id}>
                  {ws.city} — {ws.name} ({ws.address || 'Адрес не указан'})
                </option>
              ))}
            </select>
            {errors.workshop_id && <p className="text-danger text-xs mt-1">{errors.workshop_id.message}</p>}
          </div>
          {workshops.length === 0 && (
            <p className="text-gray-400 text-sm mt-2">Загрузка мастерских...</p>
          )}
        </div>

        {/* Car info */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">🚗 Автомобиль</h2>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Марка *</label>
              <input {...register('car_brand')} placeholder="Toyota" className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
              {err('car_brand')}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Модель *</label>
              <input {...register('car_model')} placeholder="Camry" className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
              {err('car_model')}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Год *</label>
              <input type="number" {...register('car_year', {valueAsNumber:true})} placeholder="2020"
                min={1900} max={new Date().getFullYear()}
                className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
              {err('car_year')}
            </div>
          </div>
        </div>

        {/* Services */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">Услуги *</h2>
          {services.length === 0 ? (
            <p className="text-gray-400 text-sm">Загрузка услуг...</p>
          ) : (
            <div className="space-y-2">
              {services.map((s) => (
                <label key={s.id} className="flex items-center justify-between gap-3 cursor-pointer hover:bg-gray-50 p-2 rounded-lg border border-transparent hover:border-gray-200 transition">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" value={s.id} className="accent-primary w-4 h-4"
                      checked={selectedIds.includes(s.id)}
                      onChange={(e) => {
                        const v = Number(e.target.value);
                        setValue('service_ids', e.target.checked ? [...selectedIds, v] : selectedIds.filter((id)=>id!==v), {shouldValidate:true});
                      }}
                    />
                    <span className="text-sm">{s.name}</span>
                  </div>
                  {s.price && <span className="text-sm font-medium text-gray-600">{Number(s.price).toLocaleString('ru-RU')} ₽</span>}
                </label>
              ))}
            </div>
          )}
          {errors.service_ids && <p className="text-danger text-xs mt-2">{errors.service_ids.message}</p>}
          {total > 0 && (
            <div className="mt-4 pt-3 border-t flex justify-between font-semibold">
              <span>Итого:</span><span className="text-primary-dark">{total.toLocaleString('ru-RU')} ₽</span>
            </div>
          )}
        </div>

        {/* Description */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <label className="block text-sm font-medium text-gray-700 mb-1">Описание / Пожелания</label>
          <textarea {...register('description')} rows={3}
            className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            placeholder="Опишите проблему или пожелания..." />
        </div>

        {/* ===== КАЛЕНДАРЬ ЗАПИСИ (ВНУТРИ ФОРМЫ!) ===== */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <BookingCalendar onSelectDateTime={handleSelectDateTime} />
        </div>

        {/* Отображение выбранной даты и предупреждение */}
        {selectedDateTime ? (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm flex items-center gap-2">
            <span>✅</span>
            Вы записаны на <strong>{selectedDateTime.date}</strong> в <strong>{selectedDateTime.time}</strong>
          </div>
        ) : (
          !isMaster && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm flex items-center gap-2">
              <span>⚠️</span>
              Пожалуйста, выберите дату и время записи перед оплатой
            </div>
          )
        )}

        {/* Кнопки */}
        <div className="flex gap-3">
          <button 
            type="submit" 
            disabled={saving || (!isMaster && !selectedDateTime)} 
            className={`flex-1 py-3 rounded-xl font-semibold transition ${
              saving || (!isMaster && !selectedDateTime)
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-primary text-white hover:bg-primary-dark'
            }`}
          >
            {saving ? 'Сохранение...' : (isMaster ? 'Создать заявку' : 'Далее — к оплате →')}
          </button>
          <button type="button" onClick={()=>navigate('/app/orders')}
            className="px-6 py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition">
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
}