import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ordersApi } from '../../api/ordersApi';
import { paymentsApi } from '../../api/paymentsApi';
import { useToast } from '../../components/Toast/Toast';
import { useAuthStore } from '../../store/authStore';

function maskCard(val: string) {
  const digits = val.replace(/\D/g, '').slice(0, 16);
  return digits.replace(/(.{4})/g, '$1 ').trim();
}
function maskExpiry(val: string) {
  const digits = val.replace(/\D/g, '').slice(0, 4);
  if (digits.length >= 3) return digits.slice(0,2) + '/' + digits.slice(2);
  return digits;
}

export default function PaymentPage() {
  const [draft, setDraft] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [card, setCard] = useState({ number:'', expiry:'', cvv:'', name:'' });
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { showToast, ToastContainer } = useToast();

  // Только клиенты могут видеть страницу оплаты
  useEffect(() => {
    if (user?.role === 'master' || user?.role === 'admin') {
      showToast('Мастера не нуждаются в оплате', 'error');
      navigate('/app/orders');
    }
  }, [user, navigate]);

  useEffect(() => {
    const raw = sessionStorage.getItem('orderDraft');
    if (!raw) { navigate('/app/orders/new'); return; }
    setDraft(JSON.parse(raw));
  }, [navigate]);

  const handlePay = async () => {
    if (!draft) return;
    setLoading(true);
    try {
      const orderRes = await ordersApi.create({
        car_brand: draft.car_brand, car_model: draft.car_model,
        car_year: draft.car_year, description: draft.description,
        service_ids: draft.service_ids,
      });
      const orderId = orderRes.data.id;
      await paymentsApi.stub({ order_id: orderId, amount: draft.total || 0, card_number: card.number.replace(/\s/g,'') });
      sessionStorage.removeItem('orderDraft');
      navigate('/app/orders');
      showToast(`Заявка #${orderId} успешно создана!`, 'success');
    } catch {
      showToast('Что-то пошло не так. Попробуйте ещё раз.', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (!draft) return <div className="p-12 text-center text-gray-400">Загрузка...</div>;

  const total = Number(draft.total) || 0;

  return (
    <div className="max-w-lg mx-auto">
      <ToastContainer />
      <h1 className="text-2xl font-bold text-primary-dark mb-6">Оплата услуг</h1>

      {/* Order summary */}
      <div className="bg-primary-light rounded-xl p-5 mb-6 border border-blue-200">
        <h2 className="font-semibold text-primary-dark mb-3">Ваш заказ</h2>
        <div className="space-y-1 text-sm text-gray-700">
          <p>🚗 <span className="font-medium">{draft.car_brand} {draft.car_model} {draft.car_year}</span></p>
          {draft.services && draft.services.length > 0 && (
            <div className="mt-2 space-y-1">
              {draft.services.map((s: any) => (
                <div key={s.id} className="flex justify-between">
                  <span>{s.name}</span>
                  <span className="text-gray-600">{Number(s.price).toLocaleString('ru-RU')} ₽</span>
                </div>
              ))}
            </div>
          )}
          <div className="border-t border-blue-200 mt-3 pt-3 flex justify-between font-bold text-base">
            <span>Итого:</span>
            <span className="text-primary-dark">{total.toLocaleString('ru-RU')} ₽</span>
          </div>
        </div>
      </div>

      {/* Card fields — decorative stub */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4 shadow-sm">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <span>💳</span> Данные карты
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Номер карты</label>
            <input
              type="text" placeholder="0000 0000 0000 0000"
              value={card.number}
              onChange={(e) => setCard((p) => ({ ...p, number: maskCard(e.target.value) }))}
              maxLength={19}
              className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary font-mono tracking-widest"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Срок действия</label>
              <input
                type="text" placeholder="MM/YY"
                value={card.expiry}
                onChange={(e) => setCard((p) => ({ ...p, expiry: maskExpiry(e.target.value) }))}
                maxLength={5}
                className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">CVV</label>
              <input
                type="password" placeholder="•••"
                value={card.cvv}
                onChange={(e) => setCard((p) => ({ ...p, cvv: e.target.value.replace(/\D/g,'').slice(0,3) }))}
                maxLength={3}
                className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Имя держателя</label>
            <input
              type="text" placeholder="IVAN IVANOV"
              value={card.name}
              onChange={(e) => setCard((p) => ({ ...p, name: e.target.value.toUpperCase() }))}
              className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary uppercase"
            />
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-4 flex items-center gap-1">
          🔒 Тестовый режим. Реальное списание не производится.
        </p>
      </div>

      <button
        onClick={handlePay}
        disabled={loading}
        className="w-full py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50 transition font-semibold text-base shadow-sm"
      >
        {loading ? '⏳ Обработка...' : `🔒 Оплатить ${total.toLocaleString('ru-RU')} ₽`}
      </button>
      <button onClick={() => navigate('/app/orders/new')}
        className="mt-3 w-full py-2 text-primary text-sm hover:underline">
        ← Назад к форме
      </button>
    </div>
  );
}
