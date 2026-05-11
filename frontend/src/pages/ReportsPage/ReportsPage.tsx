import { useEffect, useState } from 'react';
import api from '../../api/axiosInstance';
import { useAuthStore } from '../../store/authStore';
import { useToast } from '../../components/Toast/Toast';

export default function ReportsPage() {
  const [personal, setPersonal] = useState<any[]>([]);
  const [finance, setFinance] = useState<any>(null);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [loading, setLoading] = useState(false);
  const user = useAuthStore((s)=>s.user);
  const { showToast, ToastContainer } = useToast();

  const fetchReports = async () => {
    setLoading(true);
    try {
      const params: Record<string,string> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const [p, f] = await Promise.all([
        api.get('/reports/personal', { params }),
        user?.role === 'admin' ? api.get('/reports/finance', { params }) : Promise.resolve(null),
      ]);
      setPersonal(p.data);
      if (f) setFinance(f.data);
    } catch { showToast('Ошибка загрузки отчётов','error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchReports(); }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <ToastContainer />
      <h1 className="text-2xl font-bold text-primary-dark mb-6">Отчёты</h1>

      {/* Date filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 flex flex-wrap gap-3 items-end shadow-sm">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">С</label>
          <input type="date" value={dateFrom} onChange={(e)=>setDateFrom(e.target.value)}
            className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">По</label>
          <input type="date" value={dateTo} onChange={(e)=>setDateTo(e.target.value)}
            className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" />
        </div>
        <button onClick={fetchReports} disabled={loading}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 transition">
          {loading?'Загрузка...':'Применить'}
        </button>
        {(dateFrom||dateTo) && (
          <button onClick={()=>{setDateFrom('');setDateTo('');}}
            className="px-3 py-2 text-gray-500 hover:text-danger border rounded-lg">✕</button>
        )}
      </div>

      {/* Finance (Admin only) */}
      {user?.role === 'admin' && finance && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <p className="text-sm text-gray-500 mb-1">Всего платежей</p>
            <p className="text-3xl font-bold text-primary-dark">{finance.payments_count}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <p className="text-sm text-gray-500 mb-1">Сумма платежей</p>
            <p className="text-3xl font-bold text-green-600">{Number(finance.total_payments).toLocaleString('ru-RU')} ₽</p>
          </div>
        </div>
      )}

      {/* Personal report */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div className="p-4 bg-primary-light border-b">
          <h2 className="font-semibold text-primary-dark">Отчёт по мастерам</h2>
        </div>
        {loading ? (
          <div className="p-12 text-center text-gray-400">Загрузка...</div>
        ) : personal.length === 0 ? (
          <div className="p-12 text-center text-gray-400">
            <p className="text-3xl mb-2">📊</p>
            <p>Данных за выбранный период нет</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-primary-light border-b">
                {['Мастер','Выполнено заявок'].map(h=>(
                  <th key={h} className="p-3 text-left text-sm font-semibold text-primary-dark">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {personal.map((r,i) => (
                <tr key={r.master_id} className={`border-b hover:bg-gray-50 ${i%2===1?'bg-gray-50/40':''}`}>
                  <td className="p-3 text-sm font-medium">{r.master}</td>
                  <td className="p-3">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">{r.orders_count}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
