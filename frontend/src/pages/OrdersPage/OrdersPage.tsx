import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ordersApi } from '../../api/ordersApi';
import { servicesApi } from '../../api/servicesApi';
import { workersApi, Worker } from '../../api/workersApi';
import { workshopsApi } from '../../api/workshopsApi';
import { useAuthStore } from '../../store/authStore';
import { useToast } from '../../components/Toast/Toast';
import StarRating from '../../components/StarRating';
import OrderChat from '../../components/OrderChat';

const STATUS_LABELS: Record<string, string> = { new: 'Новая', in_progress: 'В работе', done: 'Готово' };
const STATUS_COLORS: Record<string, string> = {
  new: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-800',
  done: 'bg-green-100 text-green-800',
};

interface Order {
  id: number;
  client_id: number;
  master_id: number | null;
  workshop_id: number;
  workshop?: { id: number; name: string; city: string; address: string; phone: string } | null;
  car_brand: string;
  car_model: string;
  car_year: number;
  description: string | null;
  status: string;
  created_at: string;
  client: { id: number; first_name: string; last_name: string; phone: string | null } | null;
  master: { id: number; first_name: string; last_name: string } | null;
  order_services: { service_id: number; service: { id: number; name: string; price: number } | null }[];
  workers?: Array<{ id: number; first_name: string; last_name: string }>;
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [workshops, setWorkshops] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [workshopFilter, setWorkshopFilter] = useState<number | string>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const [showEditModal, setShowEditModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [showChatModal, setShowChatModal] = useState(false);

  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [services, setServices] = useState<any[]>([]);
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [editData, setEditData] = useState<any>({});
  const [statusData, setStatusData] = useState({ status: '', worker_id: '' });
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  
  // Статусы оплаты
  const [paymentStatuses, setPaymentStatuses] = useState<Record<number, string>>(() => {
    const saved = localStorage.getItem('paymentStatuses');
    return saved ? JSON.parse(saved) : {};
  });
  
  // Оценки мастеров
  const [ratings, setRatings] = useState<Record<number, number>>(() => {
    const saved = localStorage.getItem('masterRatings');
    return saved ? JSON.parse(saved) : {};
  });

  const user = useAuthStore((s) => s.user);
  const { showToast, ToastContainer } = useToast();

  // Функция для получения города по ID мастерской (временное решение)
  const getWorkshopCity = (workshopId: number) => {
    const map: Record<number, string> = {
      172: 'Москва',
      173: 'Москва',
      174: 'Санкт-Петербург',
      175: 'Санкт-Петербург',
      176: 'Новосибирск',
      177: 'Казань',
      178: 'Екатеринбург',
    };
    return map[workshopId] || 'Неизвестно';
  };

  const getWorkshopName = (workshopId: number) => {
    const map: Record<number, string> = {
      172: 'Москва — Центральная',
      173: 'Москва — Юг',
      174: 'Санкт-Петербург — Невский',
      175: 'Санкт-Петербург — Васильевский',
      176: 'Новосибирск — Центр',
      177: 'Казань — Волга',
      178: 'Екатеринбург — Урал',
    };
    return map[workshopId] || 'Мастерская';
  };

  useEffect(() => {
    if (user?.role === 'admin') {
      workshopsApi.list().then((r) => setWorkshops(r.data)).catch(() => {});
    }
  }, [user]);

  const fetchOrders = useCallback(async () => {
    if (!user) { setLoading(false); return; }
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      if (workshopFilter) params.workshop_id = String(workshopFilter);
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = user.role === 'client' ? await ordersApi.listMy() : await ordersApi.list(params);
      setOrders(Array.isArray(res.data) ? res.data : []);
    } catch {
      showToast('Не удалось загрузить заявки', 'error');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, workshopFilter, dateFrom, dateTo, user]);

  useEffect(() => { fetchOrders(); }, [fetchOrders]);

  const openEdit = async (order: Order) => {
    setSelectedOrder(order);
    setEditData({
      client_first_name: order.client?.first_name || '',
      client_last_name: order.client?.last_name || '',
      client_phone: order.client?.phone || '',
      car_brand: order.car_brand,
      car_model: order.car_model,
      car_year: order.car_year,
      description: order.description || '',
      service_ids: order.order_services.map((os) => os.service_id),
      workshop_id: order.workshop_id,
    });
    await servicesApi.list().then((r) => setServices(r.data));
    await workshopsApi.listPublic().then((r) => setWorkshops(r.data));
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedOrder) return;
    setSaving(true);
    try {
      const payload: any = {
        client_first_name: editData.client_first_name,
        client_last_name: editData.client_last_name,
        client_phone: editData.client_phone,
        car_brand: editData.car_brand,
        car_model: editData.car_model,
        car_year: editData.car_year,
        description: editData.description || null,
        service_ids: editData.service_ids,
      };
      await ordersApi.update(selectedOrder.id, payload);
      showToast('Заявка обновлена', 'success');
      setShowEditModal(false);
      fetchOrders();
    } catch (error: any) {
      showToast('Не удалось сохранить: ' + (error?.response?.data?.detail || ''), 'error');
    } finally {
      setSaving(false);
    }
  };

  const openStatusChange = async (order: Order) => {
    setSelectedOrder(order);
    await workersApi.listByWorkshop(order.workshop_id).then((r) => setWorkers(r.data));
    let assignedWorkerId = '';
    try {
      const res = await ordersApi.getWorkers(order.id);
      const assignments = res.data || [];
      if (assignments.length > 0) {
        assignedWorkerId = String(assignments[0].worker_id);
      }
    } catch (e) {
      // нет назначений
    }
    setStatusData({ status: order.status, worker_id: assignedWorkerId });
    setShowStatusModal(true);
  };

  const handleSaveStatus = async () => {
    if (!selectedOrder) return;
    setSaving(true);
    try {
      const payload: any = { status: statusData.status };
      if (statusData.status === 'in_progress' && user?.role === 'master') {
        payload.master_id = user.id;
      }
      await ordersApi.update(selectedOrder.id, payload);
      if (statusData.worker_id) {
        try {
          await ordersApi.assignWorker(selectedOrder.id, Number(statusData.worker_id));
        } catch (assignError: any) {
          if (assignError?.response?.status !== 400) {
            console.warn('Не удалось назначить техника:', assignError);
          }
        }
      }
      showToast(`Статус изменён на "${STATUS_LABELS[statusData.status]}"`, 'success');
      setShowStatusModal(false);
      fetchOrders();
    } catch {
      showToast('Не удалось изменить статус', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (order: Order) => {
    if (!window.confirm(`Удалить заявку #${order.id}?`)) return;
    setDeleting(order.id);
    try {
      await ordersApi.delete(order.id);
      showToast(`Заявка #${order.id} удалена`, 'success');
      fetchOrders();
    } catch (e: any) {
      showToast(e?.response?.data?.detail || 'Не удалось удалить', 'error');
    } finally {
      setDeleting(null);
    }
  };

  const copyPhone = (phone: string | null) => {
    if (!phone) { showToast('Телефон не указан', 'error'); return; }
    navigator.clipboard.writeText(phone);
    showToast('Телефон скопирован', 'success');
  };

  const isMasterOrAdmin = user?.role === 'master' || user?.role === 'admin';

  const updatePaymentStatus = (orderId: number, status: string) => {
    const newStatuses = { ...paymentStatuses, [orderId]: status };
    setPaymentStatuses(newStatuses);
    localStorage.setItem('paymentStatuses', JSON.stringify(newStatuses));
  };

  const updateRating = (orderId: number, rating: number) => {
    const newRatings = { ...ratings, [orderId]: rating };
    setRatings(newRatings);
    localStorage.setItem('masterRatings', JSON.stringify(newRatings));
    showToast(`Спасибо за оценку ${rating}★`, 'success');
  };

  return (
    <div className="max-w-7xl mx-auto">
      <ToastContainer />

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-primary-dark">📋 Заявки</h1>
        <Link to="/app/orders/new" className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-medium">
          + Создать заявку
        </Link>
      </div>

      {isMasterOrAdmin && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex flex-wrap gap-3 shadow-sm">
          <input type="text" placeholder="🔍 Поиск по клиенту или авто..." value={search} onChange={(e) => setSearch(e.target.value)}
            className="border rounded-lg px-3 py-2 flex-1 min-w-44 focus:outline-none focus:ring-2 focus:ring-primary" />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary">
            <option value="">Все статусы</option>
            {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          {user?.role === 'admin' && (
            <select value={workshopFilter} onChange={(e) => setWorkshopFilter(Number(e.target.value) || '')}
              className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary">
              <option value="">Все мастерские</option>
              {workshops.map((ws) => (
                <option key={ws.id} value={ws.id}>{ws.city} — {ws.name}</option>
              ))}
            </select>
          )}
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
            className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
            className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
          {(search || statusFilter || workshopFilter || dateFrom || dateTo) && (
            <button onClick={() => { setSearch(''); setStatusFilter(''); setWorkshopFilter(''); setDateFrom(''); setDateTo(''); }}
              className="px-3 py-2 text-gray-500 hover:text-danger border rounded-lg">✕ Сбросить</button>
          )}
        </div>
      )}

      {/* Таблица заявок */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-gray-400">Загрузка...</div>
        ) : orders.length === 0 ? (
          <div className="p-12 text-center text-gray-400">
            <p className="text-4xl mb-3">📋</p><p>Заявок не найдено</p>
          </div>
        ) : (
          <table className="w-full min-w-[900px]">
            <thead>
              <tr className="bg-primary-light border-b border-gray-200">
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">ID</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Дата</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Статус</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Оплата</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Мастерская</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Клиент</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Автомобиль</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Услуги</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Оценка</th>
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Чат</th>
                {isMasterOrAdmin && <th className="p-3 text-left text-sm font-semibold text-primary-dark">Действия</th>}
              </tr>
            </thead>
            <tbody>
              {orders.map((o, i) => (
                <tr key={o.id} className={`border-b hover:bg-blue-50/30 transition ${i % 2 === 1 ? 'bg-gray-50/40' : ''}`}>
                  <td className="p-3 text-sm font-mono text-gray-500">#{o.id}</td>
                  <td className="p-3 text-sm text-gray-600 whitespace-nowrap">{new Date(o.created_at).toLocaleDateString('ru-RU')}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[o.status] || 'bg-gray-100'}`}>
                      {STATUS_LABELS[o.status] || o.status}
                    </span>
                  </td>
                  <td className="p-3 text-sm">
                    <select
                      value={paymentStatuses[o.id] || 'unpaid'}
                      onChange={(e) => updatePaymentStatus(o.id, e.target.value)}
                      className={`text-xs rounded px-2 py-1 border ${
                        (paymentStatuses[o.id] || 'unpaid') === 'paid' ? 'bg-green-50 text-green-700 border-green-300' :
                        (paymentStatuses[o.id] || 'unpaid') === 'partial' ? 'bg-yellow-50 text-yellow-700 border-yellow-300' :
                        'bg-red-50 text-red-700 border-red-300'
                      }`}
                    >
                      <option value="unpaid">❌ Не оплачено</option>
                      <option value="partial">⚠️ Частично</option>
                      <option value="paid">✅ Оплачено</option>
                    </select>
                  </td>
                  {/* Мастерская — с fallback на ID если нет объекта workshop */}
                  <td className="p-3 text-sm">
                    {o.workshop ? (
                      <div>
                        <div className="font-medium">{o.workshop.name}</div>
                        <div className="text-xs text-gray-500">{o.workshop.city}</div>
                      </div>
                    ) : (
                      <div>
                        <div className="font-medium">{getWorkshopName(o.workshop_id)}</div>
                        <div className="text-xs text-gray-500">{getWorkshopCity(o.workshop_id)}</div>
                      </div>
                    )}
                  </td>
                  <td className="p-3 text-sm">{o.client ? `${o.client.last_name} ${o.client.first_name}` : '—'}</td>
                  <td className="p-3 text-sm whitespace-nowrap">{o.car_brand} {o.car_model} {o.car_year}</td>
                  <td className="p-3 text-sm text-gray-600 max-w-[200px]">
                    <span className="block truncate">{o.order_services.map(os => os.service?.name).filter(Boolean).join(', ') || '—'}</span>
                  </td>
                  <td className="p-3">
                    <StarRating
                      rating={ratings[o.id] || 0}
                      onRate={(value) => updateRating(o.id, value)}
                      readonly={o.status !== 'done'}
                      size="sm"
                    />
                  </td>
                  {/* Кнопка чата для всех пользователей */}
                  <td className="p-3">
                    <button 
                      onClick={() => { setSelectedOrder(o); setShowChatModal(true); }}
                      className="px-2 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600 transition whitespace-nowrap"
                    >
                      💬 Чат
                    </button>
                  </td>
                  {isMasterOrAdmin && (
                    <td className="p-3">
                      <div className="flex gap-1 flex-wrap">
                        {o.status !== 'done' && (
                          <>
                            <button onClick={() => openEdit(o)} className="px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition">
                              ✏️ Ред.
                            </button>
                            <button onClick={() => openStatusChange(o)} className="px-2 py-1 bg-amber-500 text-white text-xs rounded hover:bg-amber-600 transition">
                              🔄 Статус
                            </button>
                          </>
                        )}
                        {o.status === 'done' && (
                          <button onClick={() => { setSelectedOrder(o); setShowContactModal(true); }}
                            className="px-2 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition">
                            📞 Связаться
                          </button>
                        )}
                        <button onClick={() => handleDelete(o)} disabled={deleting === o.id}
                          className="px-2 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition disabled:opacity-50">
                          🗑️
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

      {/* ===== МОДАЛЬНОЕ ОКНО РЕДАКТИРОВАНИЯ ===== */}
      {showEditModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold text-primary-dark">✏️ Редактирование заявки #{selectedOrder.id}</h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <h3 className="font-semibold text-blue-800 mb-3">👤 Данные клиента</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Фамилия *</label>
                    <input value={editData.client_last_name} onChange={(e) => setEditData({ ...editData, client_last_name: e.target.value })}
                      className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Имя *</label>
                    <input value={editData.client_first_name} onChange={(e) => setEditData({ ...editData, client_first_name: e.target.value })}
                      className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
                <div className="mt-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">📞 Телефон</label>
                  <input value={editData.client_phone} onChange={(e) => setEditData({ ...editData, client_phone: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="+7 999 123-45-67" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">🏭 Мастерская *</label>
                <select value={editData.workshop_id} onChange={(e) => setEditData({ ...editData, workshop_id: Number(e.target.value) })}
                  className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary bg-white">
                  {workshops.map((ws) => (
                    <option key={ws.id} value={ws.id}>
                      {ws.city} — {ws.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Марка *</label>
                  <input value={editData.car_brand} onChange={(e) => setEditData({ ...editData, car_brand: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Модель *</label>
                  <input value={editData.car_model} onChange={(e) => setEditData({ ...editData, car_model: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Год *</label>
                  <input type="number" value={editData.car_year} onChange={(e) => setEditData({ ...editData, car_year: Number(e.target.value) })}
                    className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">🔧 Услуги</label>
                <div className="space-y-2 max-h-48 overflow-y-auto border rounded-lg p-3">
                  {services.map((s) => (
                    <label key={s.id} className="flex items-center justify-between gap-3 cursor-pointer hover:bg-gray-50 p-2 rounded">
                      <div className="flex items-center gap-2">
                        <input type="checkbox" checked={editData.service_ids?.includes(s.id)}
                          onChange={() => {
                            const ids = editData.service_ids || [];
                            setEditData({ ...editData, service_ids: ids.includes(s.id) ? ids.filter((id: number) => id !== s.id) : [...ids, s.id] });
                          }}
                          className="accent-primary w-4 h-4" />
                        <span className="text-sm">{s.name}</span>
                      </div>
                      {s.price && <span className="text-sm font-medium text-gray-600">{Number(s.price).toLocaleString()} ₽</span>}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">📝 Описание</label>
                <textarea value={editData.description} onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                  rows={3} className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  placeholder="Описание проблемы..." />
              </div>
            </div>
            <div className="p-6 border-t flex gap-3">
              <button onClick={handleSaveEdit} disabled={saving}
                className="flex-1 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-semibold disabled:opacity-50">
                {saving ? 'Сохранение...' : '💾 Сохранить'}
              </button>
              <button onClick={() => setShowEditModal(false)}
                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-semibold">
                ❌ Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== МОДАЛЬНОЕ ОКНО СМЕНЫ СТАТУСА ===== */}
      {showStatusModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold text-primary-dark">🔄 Смена статуса</h2>
              <p className="text-sm text-gray-500 mt-1">Заявка #{selectedOrder.id}</p>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Новый статус *</label>
                <select value={statusData.status} onChange={(e) => setStatusData({ ...statusData, status: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary bg-white">
                  {Object.entries(STATUS_LABELS).map(([k, v]) => (
                    <option key={k} value={k} disabled={k === selectedOrder.status}>{v}</option>
                  ))}
                </select>
              </div>
              {(statusData.status === 'in_progress' || selectedOrder.status === 'in_progress' || workers.length > 0) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">👷 Назначить работника</label>
                  <select value={statusData.worker_id || ''} onChange={(e) => setStatusData({ ...statusData, worker_id: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary bg-white">
                    <option value="">Не назначен</option>
                    {workers.map((w) => (
                      <option key={w.id} value={String(w.id)}>{w.last_name} {w.first_name} {w.position ? `(${w.position})` : ''}</option>
                    ))}
                  </select>
                  {selectedOrder.workers && selectedOrder.workers.length > 0 && statusData.worker_id !== '' && (
                  <p className="text-xs text-green-600 mt-1">
                    ✅ Текущий: {selectedOrder.workers[0].last_name} {selectedOrder.workers[0].first_name}
                  </p>
                )}
                </div>
              )}
            </div>
            <div className="p-6 border-t flex gap-3">
              <button onClick={handleSaveStatus} disabled={saving}
                className="flex-1 py-3 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition font-semibold disabled:opacity-50">
                {saving ? 'Сохранение...' : '✅ Сменить статус'}
              </button>
              <button onClick={() => setShowStatusModal(false)}
                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-semibold">
                ❌ Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== МОДАЛЬНОЕ ОКНО СВЯЗАТЬСЯ ===== */}
      {showContactModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold text-primary-dark">📞 Связаться с клиентом</h2>
              <p className="text-sm text-gray-500 mt-1">Заявка #{selectedOrder.id} — Готово</p>
            </div>
            <div className="p-6 space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-3">👤 Клиент</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">ФИО:</span>
                    <span className="font-medium">{selectedOrder.client ? `${selectedOrder.client.last_name} ${selectedOrder.client.first_name}` : '—'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Телефон:</span>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{selectedOrder.client?.phone || 'Не указан'}</span>
                      {selectedOrder.client?.phone && (
                        <button onClick={() => copyPhone(selectedOrder.client!.phone)}
                          className="p-1 text-blue-500 hover:bg-blue-50 rounded" title="Копировать">
                          📋
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">🚗 Автомобиль</h3>
                <p className="text-sm text-gray-600">{selectedOrder.car_brand} {selectedOrder.car_model} ({selectedOrder.car_year})</p>
              </div>
              {selectedOrder.order_services.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-800 mb-2">🔧 Выполненные услуги</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {selectedOrder.order_services.map((os) => (
                      <li key={os.service_id}>• {os.service?.name}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="p-6 border-t">
              <button onClick={() => setShowContactModal(false)}
                className="w-full py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-semibold">
                ✅ Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== МОДАЛЬНОЕ ОКНО ЧАТА ===== */}
      {showChatModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-xl">
            <div className="p-4 border-b flex justify-between items-center">
              <h2 className="text-lg font-bold text-primary-dark">
                💬 Чат по заявке #{selectedOrder.id}
              </h2>
              <button
                onClick={() => setShowChatModal(false)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ✕
              </button>
            </div>
            <div className="p-4">
              <OrderChat
                orderId={selectedOrder.id}
                currentUserName={user?.name || 'Пользователь'}
                currentUserRole={user?.role || 'client'}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}