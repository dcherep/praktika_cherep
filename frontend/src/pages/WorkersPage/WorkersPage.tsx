import { useEffect, useState } from 'react';
import { workersApi, Worker, WorkerCreate } from '../../api/workersApi';
import { workshopsApi, Workshop } from '../../api/workshopsApi';
import { useAuthStore } from '../../store/authStore';
import { useToast } from '../../components/Toast/Toast';
import WorkerScheduleModal from '../../components/WorkerScheduleModal';

const STATUS_BADGE: Record<'free' | 'assigned', string> = {
  free: 'bg-green-100 text-green-700',
  assigned: 'bg-amber-100 text-amber-800',
};

// Компонент для отображения заявок (заглушка с тестовыми данными)
const AppointmentsList = ({ workerId, date }: { workerId: number; date: string }) => {
  // Тестовые данные для демонстрации (в зависимости от дня недели)
  const getMockAppointments = (dateStr: string, workerIdNum: number) => {
    const dayOfWeek = new Date(dateStr).getDay();
    
    // Разные записи для разных дней
    if (dayOfWeek === 1) { // Понедельник
      return [
        { id: 1, time: '10:00', car: 'Toyota Camry', client: 'Иванов', status: 'new' },
        { id: 2, time: '14:30', car: 'Hyundai Solaris', client: 'Петров', status: 'in_progress' },
      ];
    } else if (dayOfWeek === 2) { // Вторник
      return [
        { id: 3, time: '09:00', car: 'Kia Rio', client: 'Сидоров', status: 'new' },
        { id: 4, time: '13:00', car: 'Renault Logan', client: 'Кузнецов', status: 'new' },
        { id: 5, time: '16:00', car: 'Lada Vesta', client: 'Михайлов', status: 'done' },
      ];
    } else if (dayOfWeek === 3) { // Среда
      return [
        { id: 6, time: '11:00', car: 'BMW X5', client: 'Соколов', status: 'in_progress' },
      ];
    } else if (dayOfWeek === 4) { // Четверг
      return [
        { id: 7, time: '12:00', car: 'Mercedes E200', client: 'Новиков', status: 'new' },
        { id: 8, time: '15:00', car: 'Audi A6', client: 'Морозов', status: 'new' },
      ];
    } else if (dayOfWeek === 5) { // Пятница
      return [
        { id: 9, time: '09:30', car: 'Volkswagen Polo', client: 'Волков', status: 'in_progress' },
        { id: 10, time: '14:00', car: 'Ford Focus', client: 'Алексеев', status: 'new' },
        { id: 11, time: '17:00', car: 'Nissan Qashqai', client: 'Лебедев', status: 'new' },
      ];
    } else if (dayOfWeek === 6) { // Суббота
      return [
        { id: 12, time: '10:30', car: 'Mazda CX-5', client: 'Егоров', status: 'new' },
      ];
    } else { // Воскресенье — выходной
      return [];
    }
  };

  const appointments = getMockAppointments(date, workerId);
  const dateObj = new Date(date);
  const isWeekend = dateObj.getDay() === 0;

  if (isWeekend) {
    return <div className="text-xs text-gray-400">Выходной день</div>;
  }

  if (appointments.length === 0) {
    return <div className="text-xs text-gray-400">Нет записей</div>;
  }

  return (
    <div className="space-y-1">
      {appointments.map((apt) => (
        <div key={apt.id} className="text-xs bg-blue-50 p-1 rounded">
          <span className="font-medium">{apt.time}</span> - {apt.car}
          <div className="text-[10px] text-gray-500">{apt.client}</div>
          <span className={`inline-block mt-1 px-1 rounded text-[10px] ${
            apt.status === 'done' ? 'bg-green-200' : 
            apt.status === 'in_progress' ? 'bg-yellow-200' : 'bg-blue-100'
          }`}>
            {apt.status === 'done' ? '✓ Готово' : 
             apt.status === 'in_progress' ? '🔄 В работе' : '○ Новая'}
          </span>
        </div>
      ))}
    </div>
  );
};

export default function WorkersPage() {
  const { user } = useAuthStore();
  const { showToast, ToastContainer } = useToast();

  const [workers, setWorkers] = useState<Worker[]>([]);
  const [workshops, setWorkshops] = useState<Workshop[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedWorkerForSchedule, setSelectedWorkerForSchedule] = useState<{ id: number; name: string } | null>(null);
  const [editing, setEditing] = useState<Worker | null>(null);
  const [form, setForm] = useState<WorkerCreate>({ first_name: '', last_name: '', position: '', workshop_id: null });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);

  const isAdmin = user?.role === 'admin';
  const isMaster = user?.role === 'master';

  const fetchData = async () => {
    setLoading(true);
    try {
      const [wRes, wsRes] = await Promise.all([
        workersApi.list(),
        isAdmin ? workshopsApi.list() : Promise.resolve({ data: [] as Workshop[] }),
      ]);
      setWorkers(wRes.data);
      if (isAdmin) setWorkshops(wsRes.data);
    } catch {
      showToast('Не удалось загрузить работников', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ first_name: '', last_name: '', position: '', workshop_id: null });
    setError('');
    setShowModal(true);
  };

  const openEdit = (w: Worker) => {
    setEditing(w);
    setForm({
      first_name: w.first_name,
      last_name: w.last_name,
      position: w.position || '',
      workshop_id: w.workshop_id,
    });
    setError('');
    setShowModal(true);
  };

  const openSchedule = (w: Worker) => {
    setSelectedWorkerForSchedule({ id: w.id, name: `${w.last_name} ${w.first_name}` });
    setShowScheduleModal(true);
  };

  const setField = (k: keyof WorkerCreate, v: any) =>
    setForm((p) => ({ ...p, [k]: v }));

  const handleSave = async () => {
    if (!form.first_name || !form.last_name) {
      setError('Заполните имя и фамилию');
      return;
    }
    setSaving(true);
    setError('');
    try {
      if (editing) {
        await workersApi.update(editing.id, {
          first_name: form.first_name,
          last_name: form.last_name,
          position: form.position,
        });
        showToast('Работник обновлён', 'success');
      } else {
        await workersApi.create({
          first_name: form.first_name,
          last_name: form.last_name,
          position: form.position,
          workshop_id: isAdmin ? form.workshop_id ?? undefined : undefined,
        });
        showToast('Работник создан', 'success');
      }
      setShowModal(false);
      fetchData();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (w: Worker) => {
    try {
      await workersApi.update(w.id, { is_active: !w.is_active });
      fetchData();
    } catch {
      showToast('Не удалось изменить статус', 'error');
    }
  };

  // Получить следующие 7 дней
  const getNextDays = () => {
    const days = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date();
      d.setDate(d.getDate() + i);
      days.push(d.toISOString().split('T')[0]);
    }
    return days;
  };

  const nextDays = getNextDays();

  return (
    <div className="max-w-7xl mx-auto">
      <ToastContainer />
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-primary-dark">
          {isMaster ? 'Расписание мастеров' : 'Работники'}
        </h1>
        {isAdmin && (
          <button
            onClick={openCreate}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-medium"
          >
            + Добавить работника
          </button>
        )}
      </div>

      {/* Выбор даты для просмотра расписания */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 shadow-sm">
        <div className="text-sm font-medium text-gray-700 mb-2">📅 Выберите дату:</div>
        <div className="grid grid-cols-7 gap-2">
          {nextDays.map((date) => (
            <button
              key={date}
              onClick={() => setSelectedDate(date)}
              className={`p-2 rounded-lg text-center text-sm transition ${
                selectedDate === date
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              <div className="text-xs">
                {new Date(date).toLocaleDateString('ru', { weekday: 'short' })}
              </div>
              <div className="font-bold">{new Date(date).getDate()}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Таблица работников и их записей */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-gray-400">Загрузка...</div>
        ) : workers.length === 0 ? (
          <div className="p-12 text-center text-gray-400">Работников пока нет</div>
        ) : (
          <table className="w-full min-w-[800px]">
            <thead>
              <tr className="bg-primary-light border-b">
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">ID</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">ФИО</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Должность</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Мастерская</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Статус</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Записи на {new Date(selectedDate).toLocaleDateString('ru')}</th>
                {isAdmin && <th className="p-3 text-left text-sm font-semibold text-primary-dark">Действия</th>}
              </tr>
            </thead>
            <tbody>
              {workers.map((w, i) => (
                <tr
                  key={w.id}
                  className={`border-b hover:bg-gray-50 transition ${i % 2 === 1 ? 'bg-gray-50/40' : ''}`}
                >
                  <td className="p-3 text-sm text-gray-500">#{w.id}</td>
                  <td className="p-3 text-sm font-medium">
                    {w.last_name} {w.first_name}
                  </td>
                  <td className="p-3 text-sm text-gray-600">{w.position || '—'}</td>
                  <td className="p-3 text-sm text-gray-600">
                    {isAdmin
                      ? workshops.find((ws) => ws.id === w.workshop_id)
                        ? `${workshops.find((ws) => ws.id === w.workshop_id)!.city} — ${
                            workshops.find((ws) => ws.id === w.workshop_id)!.name
                          }`
                        : `ID ${w.workshop_id}`
                      : 'Моя мастерская'}
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        STATUS_BADGE[w.is_assigned ? 'assigned' : 'free']
                      }`}
                    >
                      {w.is_assigned ? 'Назначен' : 'Не назначен'}
                    </span>
                  </td>
                  <td className="p-3">
                    <AppointmentsList workerId={w.id} date={selectedDate} />
                  </td>
                  {isAdmin && (
                    <td className="p-3">
                      <div className="flex gap-2 flex-wrap">
                        <button
                          onClick={() => openSchedule(w)}
                          className="px-2 py-1 border border-blue-300 text-blue-600 text-xs rounded hover:bg-blue-50 transition"
                        >
                          📅 Расписание
                        </button>
                        <button
                          onClick={() => openEdit(w)}
                          className="px-2 py-1 border border-primary text-primary text-xs rounded hover:bg-primary-light transition"
                        >
                          Изменить
                        </button>
                        <button
                          onClick={() => toggleActive(w)}
                          className="px-2 py-1 border border-gray-300 text-xs rounded hover:bg-gray-50 transition"
                        >
                          {w.is_active ? 'Деактивировать' : 'Активировать'}
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Модальное окно создания/редактирования работника */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="p-5 border-b flex justify-between items-center">
              <h2 className="text-lg font-bold text-primary-dark">
                {editing ? 'Редактировать работника' : 'Новый работник'}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">
                ✕
              </button>
            </div>
            <div className="p-5 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Фамилия *</label>
                  <input
                    value={form.last_name}
                    onChange={(e) => setField('last_name', e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Имя *</label>
                  <input
                    value={form.first_name}
                    onChange={(e) => setField('first_name', e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Должность</label>
                <input
                  value={form.position}
                  onChange={(e) => setField('position', e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              {isAdmin && (
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Мастерская *</label>
                  <select
                    value={form.workshop_id ?? ''}
                    onChange={(e) =>
                      setField('workshop_id', e.target.value ? Number(e.target.value) : null)
                    }
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="">— выберите мастерскую —</option>
                    {workshops.map((ws) => (
                      <option key={ws.id} value={ws.id}>
                        {ws.city} — {ws.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {error && <p className="text-danger text-sm bg-red-50 p-2 rounded">{error}</p>}
            </div>
            <div className="p-5 border-t flex gap-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 font-medium transition"
              >
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно расписания */}
      {showScheduleModal && selectedWorkerForSchedule && (
        <WorkerScheduleModal
          workerId={selectedWorkerForSchedule.id}
          workerName={selectedWorkerForSchedule.name}
          onClose={() => setShowScheduleModal(false)}
        />
      )}
    </div>
  );
}