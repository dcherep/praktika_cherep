import { useEffect, useState } from 'react';
import { usersApi, UserCreate } from '../../api/usersApi';
import { useToast } from '../../components/Toast/Toast';
import { workshopsApi, Workshop } from '../../api/workshopsApi';

const ROLE_LABELS: Record<number,string> = { 1:'Клиент', 2:'Мастер смены', 3:'Администратор' };
const ROLE_COLORS: Record<number,string> = { 1:'bg-gray-100 text-gray-700', 2:'bg-blue-100 text-blue-800', 3:'bg-purple-100 text-purple-800' };

interface User {
  id:number;
  first_name:string;
  last_name:string;
  middle_name:string|null;
  email:string;
  phone:string|null;
  role_id:number;
  role:{id:number;name:string}|null;
  workshops: Array<{id:number; name:string; city:string}> | [];
  is_active:boolean;
}

const EMPTY_FORM: UserCreate & {password_confirm?:string} = {
  first_name:'',
  last_name:'',
  middle_name:'',
  email:'',
  phone:'',
  password:'',
  role_id:1,
  workshop_ids: [],
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [workshops, setWorkshops] = useState<Workshop[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState<User|null>(null);
  const [form, setForm] = useState<any>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const { showToast, ToastContainer } = useToast();

  const fetchUsers = async () => {
    setLoading(true);
    try { const r = await usersApi.list(); setUsers(r.data); }
    catch { showToast('Не удалось загрузить пользователей','error'); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchUsers();
    workshopsApi.list()
      .then((r) => setWorkshops(r.data))
      .catch(() => {/* ignore, уже покажем ошибку на списке пользователей при необходимости */});
  }, []);

  const openCreate = () => { setEditUser(null); setForm(EMPTY_FORM); setFormError(''); setShowModal(true); };
  const openEdit = (u: User) => {
    setEditUser(u);
    setForm({
      first_name:u.first_name,
      last_name:u.last_name,
      middle_name:u.middle_name||'',
      email:u.email,
      phone:u.phone||'',
      password:'',
      role_id:u.role_id,
      workshop_id:u.workshop_id ?? null,
    });
    setFormError('');
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!form.first_name || !form.last_name || !form.email) { setFormError('Заполните обязательные поля'); return; }
    if (!editUser && !form.password) { setFormError('Введите пароль'); return; }
    setSaving(true); setFormError('');
    try {
      if (editUser) {
        const data: any = {
          first_name:form.first_name,
          last_name:form.last_name,
          middle_name:form.middle_name||null,
          email:form.email,
          phone:form.phone||null,
          role_id:Number(form.role_id),
          workshop_id: form.role_id === 3 ? null : (form.workshop_id ? Number(form.workshop_id) : null),
        };
        if (form.password) data.password = form.password;
        await usersApi.update(editUser.id, data);
        showToast('Пользователь обновлён','success');
      } else {
        await usersApi.create({
          ...form,
          role_id:Number(form.role_id),
          middle_name:form.middle_name||null,
          phone:form.phone||null,
          workshop_id: form.role_id === 3 ? null : (form.workshop_id ? Number(form.workshop_id) : null),
        });
        showToast('Пользователь создан','success');
      }
      setShowModal(false); fetchUsers();
    } catch (e:any) { setFormError(e?.response?.data?.detail || 'Ошибка сохранения'); }
    finally { setSaving(false); }
  };

  const handleDeactivate = async (u: User) => {
    if (!window.confirm(`Деактивировать пользователя ${u.last_name} ${u.first_name}?`)) return;
    try {
      await usersApi.deactivate(u.id);
      showToast('Пользователь деактивирован','success'); fetchUsers();
    } catch { showToast('Ошибка','error'); }
  };

  const set = (k:string, v:any) => setForm((p:any) => ({...p,[k]:v}));

  return (
    <div className="max-w-5xl mx-auto">
      <ToastContainer />
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-primary-dark">Пользователи</h1>
        <button onClick={openCreate} className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition font-medium">
          + Добавить пользователя
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-gray-400">Загрузка...</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-primary-light border-b">
                {['ID','ФИО','Email','Телефон','Мастерская','Роль','Статус','Действия'].map(h=>(
                  <th key={h} className="p-3 text-left text-sm font-semibold text-primary-dark">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u,i) => (
                <tr key={u.id} className={`border-b hover:bg-gray-50 ${i%2===1?'bg-gray-50/40':''}`}>
                  <td className="p-3 text-sm text-gray-500">#{u.id}</td>
                  <td className="p-3 text-sm font-medium">{u.last_name} {u.first_name} {u.middle_name||''}</td>
                  <td className="p-3 text-sm text-gray-600">{u.email}</td>
                  <td className="p-3 text-sm text-gray-600">{u.phone||'—'}</td>
                  <td className="p-3 text-sm text-gray-600">
                    {u.workshop
                      ? `${u.workshop.city} — ${u.workshop.name}`
                      : (u.role_id === 3 ? 'Все мастерские' : '—')}
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${ROLE_COLORS[u.role_id]||'bg-gray-100'}`}>
                      {ROLE_LABELS[u.role_id]||u.role?.name||'—'}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${u.is_active?'bg-green-100 text-green-700':'bg-red-100 text-red-700'}`}>
                      {u.is_active?'Активен':'Деактивирован'}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button onClick={()=>openEdit(u)}
                        className="px-2 py-1 border border-primary text-primary text-xs rounded hover:bg-primary-light transition">
                        Изменить
                      </button>
                      {u.is_active && (
                        <button onClick={()=>handleDeactivate(u)}
                          className="px-2 py-1 border border-danger text-danger text-xs rounded hover:bg-red-50 transition">
                          Деактивировать
                        </button>
                      )}
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
              <h2 className="text-lg font-bold text-primary-dark">{editUser ? 'Редактировать' : 'Новый пользователь'}</h2>
              <button onClick={()=>setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            <div className="p-5 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Фамилия *</label>
                  <input value={form.last_name} onChange={(e)=>set('last_name',e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Имя *</label>
                  <input value={form.first_name} onChange={(e)=>set('first_name',e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Отчество</label>
                <input value={form.middle_name} onChange={(e)=>set('middle_name',e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Email *</label>
                <input type="email" value={form.email} onChange={(e)=>set('email',e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Телефон</label>
                <input value={form.phone} onChange={(e)=>set('phone',e.target.value)} placeholder="+7..." className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Мастерская</label>
                <select
                  value={form.workshop_id ?? ''}
                  onChange={(e)=>set('workshop_id', e.target.value ? Number(e.target.value) : null)}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={Number(form.role_id) === 3}
                >
                  {Number(form.role_id) === 3 ? (
                    <option value="">Глобальный администратор</option>
                  ) : (
                    <>
                      <option value="">— выберите мастерскую —</option>
                      {workshops.map((w)=>(
                        <option key={w.id} value={w.id}>{w.city} — {w.name}</option>
                      ))}
                    </>
                  )}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Роль *</label>
                <select value={form.role_id} onChange={(e)=>set('role_id',e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                  <option value={1}>Клиент</option>
                  <option value={2}>Мастер смены</option>
                  <option value={3}>Администратор</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Пароль {editUser?'(оставьте пустым, чтобы не менять)':'*'}</label>
                <input type="password" value={form.password} onChange={(e)=>set('password',e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
              </div>
              {formError && <p className="text-danger text-sm bg-red-50 p-2 rounded">{formError}</p>}
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
