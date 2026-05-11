import { useEffect, useState } from 'react';
import { workerSchedulesApi, WorkerSchedule, WorkerScheduleCreate } from '../api/workerSchedulesApi';
import { useToast } from './Toast/Toast';

interface WorkerScheduleModalProps {
  workerId: number;
  workerName: string;
  onClose: () => void;
}

const SHIFT_TYPES = [
  { value: 'full', label: 'Полная (8ч)' },
  { value: 'morning', label: 'Утренняя (08:00-16:00)' },
  { value: 'evening', label: 'Вечерняя (16:00-00:00)' },
  { value: 'night', label: 'Ночная (00:00-08:00)' },
  { value: 'half', label: 'Половина (4ч)' },
];

export default function WorkerScheduleModal({ workerId, workerName, onClose }: WorkerScheduleModalProps) {
  const { showToast } = useToast();
  const [schedules, setSchedules] = useState<WorkerSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    fetchSchedules();
  }, [workerId]);

  const fetchSchedules = async () => {
    setLoading(true);
    try {
      const res = await workerSchedulesApi.getByWorker(workerId);
      setSchedules(res.data);
    } catch {
      showToast('Не удалось загрузить расписание', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (scheduleData: Partial<WorkerScheduleCreate>) => {
    setSaving(true);
    try {
      await workerSchedulesApi.create({
        worker_id: workerId,
        date: selectedDate,
        shift_type: scheduleData.shift_type || 'full',
        hours: scheduleData.hours || 8,
        is_working: scheduleData.is_working ?? true,
        comment: scheduleData.comment || '',
      });
      showToast('Расписание сохранено', 'success');
      fetchSchedules();
    } catch {
      showToast('Не удалось сохранить расписание', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (scheduleId: number) => {
    if (!confirm('Удалить эту запись из расписания?')) return;
    try {
      await workerSchedulesApi.delete(scheduleId);
      showToast('Запись удалена', 'success');
      fetchSchedules();
    } catch {
      showToast('Не удалось удалить', 'error');
    }
  };

  const getScheduleForDate = (date: string) => {
    return schedules.find((s) => s.date === date);
  };

  const currentSchedule = getScheduleForDate(selectedDate);

  // Генерация дат на 2 недели вперёд
  const dates = [];
  const today = new Date();
  for (let i = 0; i < 14; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    dates.push(date.toISOString().split('T')[0]);
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl my-8">
        <div className="p-5 border-b flex justify-between items-center">
          <div>
            <h2 className="text-lg font-bold text-primary-dark">Расписание работника</h2>
            <p className="text-sm text-gray-500">{workerName}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">
            ✕
          </button>
        </div>

        <div className="p-5">
          {/* Календарь на 2 недели */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Выберите дату:</h3>
            <div className="grid grid-cols-7 gap-2">
              {dates.map((date) => {
                const d = new Date(date);
                const dayName = d.toLocaleDateString('ru-RU', { weekday: 'short' });
                const dayNum = d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'numeric' });
                const schedule = getScheduleForDate(date);
                const isWeekend = d.getDay() === 0 || d.getDay() === 6;
                const isSelected = date === selectedDate;

                return (
                  <button
                    key={date}
                    onClick={() => setSelectedDate(date)}
                    className={`p-2 rounded-lg border text-center transition ${
                      isSelected
                        ? 'bg-primary text-white border-primary'
                        : schedule
                        ? schedule.is_working
                          ? 'bg-green-50 border-green-300 hover:bg-green-100'
                          : 'bg-red-50 border-red-300 hover:bg-red-100'
                        : isWeekend
                        ? 'bg-gray-100 border-gray-300'
                        : 'bg-white border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="text-xs font-medium">{dayName}</div>
                    <div className="text-sm font-bold">{dayNum}</div>
                    {schedule && (
                      <div className="text-xs mt-1">
                        {schedule.is_working ? '📅' : '❌'}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Информация о выбранном дне */}
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              {new Date(selectedDate).toLocaleDateString('ru-RU', {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
              })}
            </h3>

            {loading ? (
              <div className="text-center text-gray-400 py-4">Загрузка...</div>
            ) : currentSchedule ? (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      currentSchedule.is_working
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {currentSchedule.is_working ? 'Рабочий день' : 'Выходной'}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDelete(currentSchedule.id)}
                    className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm transition"
                  >
                    Удалить
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Тип смены:</span>{' '}
                    <span className="font-medium">
                      {SHIFT_TYPES.find((s) => s.value === currentSchedule.shift_type)?.label || currentSchedule.shift_type}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Часов:</span>{' '}
                    <span className="font-medium">{currentSchedule.hours} ч.</span>
                  </div>
                  {currentSchedule.comment && (
                    <div className="col-span-2">
                      <span className="text-gray-500">Комментарий:</span>{' '}
                      <span className="font-medium">{currentSchedule.comment}</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-4">
                Нет записи на этот день
              </div>
            )}
          </div>

          {/* Форма добавления/редактирования */}
          {!currentSchedule && (
            <div className="border-t pt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Добавить запись:</h3>
              <ScheduleForm
                onSave={handleSave}
                onCancel={onClose}
                saving={saving}
                selectedDate={selectedDate}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Компонент формы
function ScheduleForm({
  onSave,
  onCancel,
  saving,
  selectedDate,
}: {
  onSave: (data: Partial<WorkerScheduleCreate>) => void;
  onCancel: () => void;
  saving: boolean;
  selectedDate: string;
}) {
  const [shift_type, setShift_type] = useState('full');
  const [hours, setHours] = useState(8);
  const [is_working, setIs_working] = useState(true);
  const [comment, setComment] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ shift_type, hours, is_working, comment });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">Тип смены</label>
        <select
          value={shift_type}
          onChange={(e) => {
            setShift_type(e.target.value);
            if (e.target.value === 'half') setHours(4);
            else if (e.target.value === 'full') setHours(8);
          }}
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {SHIFT_TYPES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">Часов</label>
        <input
          type="number"
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          min="1"
          max="24"
        />
      </div>

      <div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={is_working}
            onChange={(e) => setIs_working(e.target.checked)}
            className="w-4 h-4"
          />
          <span className="text-sm text-gray-700">Рабочий день (не галочка = выходной)</span>
        </label>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">Комментарий</label>
        <input
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="Например: отгул, праздничный день..."
        />
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={saving}
          className="flex-1 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 font-medium transition"
        >
          {saving ? 'Сохранение...' : 'Сохранить'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
        >
          Отмена
        </button>
      </div>
    </form>
  );
}
