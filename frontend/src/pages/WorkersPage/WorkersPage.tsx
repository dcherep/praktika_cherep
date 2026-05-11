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

  const isAdmin = user?.role === 'admin';

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

  return (
    <div className="max-w-5xl mx-auto">
      <ToastContainer />
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-primary-dark">Работники</h1>
        <button
          onClick={openCreate}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-medium"
        >
          + Добавить работника
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-gray-400">Загрузка...</div>
        ) : workers.length === 0 ? (
          <div className="p-12 text-center text-gray-400">Работников пока нет</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-primary-light border-b">
                {['ID', 'ФИО', 'Должность', 'Мастерская', 'Статус', 'Активность', 'Действия'].map((h) => (
                  <th key={h} className="p-3 text-left text-sm font-semibold text-primary-dark">
                    {h}
                  </th>
                ))}
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
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        w.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {w.is_active ? 'Активен' : 'Не активен'}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
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
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

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

