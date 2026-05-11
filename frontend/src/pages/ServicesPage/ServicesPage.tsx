import { useEffect, useState } from 'react';
import { servicesApi } from '../../api/servicesApi';
import { useAuthStore } from '../../store/authStore';
import { useToast } from '../../components/Toast/Toast';

interface Service { id:number; name:string; price:number|null; }

export default function ServicesPage() {
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editService, setEditService] = useState<Service|null>(null);
  const [form, setForm] = useState({ name:'', price:'' });
  const [saving, setSaving] = useState(false);
  const user = useAuthStore((s)=>s.user);
  const { showToast, ToastContainer } = useToast();
  const isAdmin = user?.role === 'admin';

  const fetchServices = async () => {
    setLoading(true);
    try { const r = await servicesApi.list(); setServices(r.data); }
    catch { showToast('Ошибка загрузки услуг','error'); }
    finally { setLoading(false); }
  };

  const sortedServices = [...services].sort((a, b) => {
    const priceA = Number(a.price) || 0;
    const priceB = Number(b.price) || 0;
    return sortOrder === 'asc' ? priceA - priceB : priceB - priceA;
  });

  useEffect(() => { fetchServices(); }, []);

  const openCreate = () => { setEditService(null); setForm({name:'',price:''}); setShowModal(true); };
  const openEdit = (s:Service) => { setEditService(s); setForm({name:s.name, price:s.price!=null?String(s.price):''}); setShowModal(true); };

  const handleSave = async () => {
    if (!form.name.trim()) { showToast('Введите название услуги','error'); return; }
    setSaving(true);
    try {
      const data = { name:form.name.trim(), price: form.price ? Number(form.price) : undefined };
      if (editService) { await servicesApi.update(editService.id, data); showToast('Услуга обновлена','success'); }
      else { await servicesApi.create(data); showToast('Услуга добавлена','success'); }
      setShowModal(false); fetchServices();
    } catch { showToast('Ошибка сохранения','error'); }
    finally { setSaving(false); }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <ToastContainer />
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-primary-dark">Услуги</h1>
        {isAdmin && (
          <button onClick={openCreate} className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-medium">
            + Добавить услугу
          </button>
        )}
      </div>

      {/* 🔥 КНОПКИ СОРТИРОВКИ (ПРАВИЛЬНОЕ МЕСТО) 🔥 */}
      <div className="flex gap-2 mb-4">
        <button 
          onClick={() => setSortOrder('asc')}
          className={`px-3 py-1 rounded text-sm ${
            sortOrder === 'asc' ? 'bg-primary text-white' : 'bg-gray-200'
          }`}
        >
          💰 От дешёвых к дорогим
        </button>
        <button 
          onClick={() => setSortOrder('desc')}
          className={`px-3 py-1 rounded text-sm ${
            sortOrder === 'desc' ? 'bg-primary text-white' : 'bg-gray-200'
          }`}
        >
          💸 От дорогих к дешёвым
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-gray-400">Загрузка...</div>
        ) : services.length === 0 ? (
          <div className="p-12 text-center text-gray-400">
            <p className="text-3xl mb-2">🔧</p><p>Услуг пока нет</p>
            {isAdmin && <button onClick={openCreate} className="mt-3 text-primary hover:underline text-sm">Добавить первую услугу</button>}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-primary-light border-b">
                <th className="p-3 text-left text-sm font-semibold text-primary-dark">Название</th>
                <th className="p-3 text-right text-sm font-semibold text-primary-dark">Стоимость</th>
                {isAdmin && <th className="p-3 text-left text-sm font-semibold text-primary-dark">Действия</th>}
               </tr>
            </thead>
            <tbody>
              {/* 🔥 ЗДЕСЬ ИСПОЛЬЗУЕМ sortedServices ВМЕСТО services 🔥 */}
              {sortedServices.map((s,i) => (
                <tr key={s.id} className={`border-b hover:bg-gray-50 ${i%2===1?'bg-gray-50/40':''}`}>
                  <td className="p-3 text-sm font-medium">{s.name}</td>
                  <td className="p-3 text-sm text-right font-mono">
                    {s.price != null ? `${Number(s.price).toLocaleString('ru-RU')} ₽` : '—'}
                  </td>
                  {isAdmin && (
                    <td className="p-3">
                      <button onClick={()=>openEdit(s)} className="px-2 py-1 border border-primary text-primary text-xs rounded hover:bg-primary-light transition">
                        Изменить
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="p-5 border-b flex justify-between items-center">
              <h2 className="text-lg font-bold text-primary-dark">{editService?'Редактировать услугу':'Новая услуга'}</h2>
              <button onClick={()=>setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Название *</label>
                <input value={form.name} onChange={(e)=>setForm(p=>({...p,name:e.target.value}))} placeholder="Замена масла"
                  className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Стоимость (₽)</label>
                <input type="number" value={form.price} onChange={(e)=>setForm(p=>({...p,price:e.target.value}))} placeholder="1500" min={0}
                  className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
              </div>
            </div>
            <div className="p-5 border-t flex gap-3">
              <button onClick={handleSave} disabled={saving}
                className="flex-1 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 font-medium transition">
                {saving?'Сохранение...':'Сохранить'}
              </button>
              <button onClick={()=>setShowModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition">Отмена</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}