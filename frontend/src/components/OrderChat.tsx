import { useState, useEffect, useRef } from 'react';

interface Message {
  id: number;
  text: string;
  sender: string;
  senderRole: 'client' | 'master' | 'admin';
  timestamp: string;
}

interface OrderChatProps {
  orderId: number;
  currentUserName: string;
  currentUserRole: string;
}

const OrderChat = ({ orderId, currentUserName, currentUserRole }: OrderChatProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Загрузка сообщений из localStorage
  useEffect(() => {
    const saved = localStorage.getItem(`chat_${orderId}`);
    if (saved) {
      setMessages(JSON.parse(saved));
    }
  }, [orderId]);

  // Автопрокрутка вниз
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Сохранение сообщений в localStorage
  const saveMessages = (newMessages: Message[]) => {
    setMessages(newMessages);
    localStorage.setItem(`chat_${orderId}`, JSON.stringify(newMessages));
  };

  const sendMessage = () => {
    if (!newMessage.trim()) return;

    const msg: Message = {
      id: Date.now(),
      text: newMessage,
      sender: currentUserName,
      senderRole: currentUserRole as 'client' | 'master' | 'admin',
      timestamp: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    };

    saveMessages([...messages, msg]);
    setNewMessage('');
  };

  const getSenderBadge = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-red-500 text-white';
      case 'master': return 'bg-blue-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getSenderIcon = (role: string) => {
    switch (role) {
      case 'admin': return '👑';
      case 'master': return '🔧';
      default: return '👤';
    }
  };

  return (
    <div className="border rounded-xl overflow-hidden bg-white shadow-sm flex flex-col h-96">
      {/* Заголовок чата */}
      <div className="bg-primary text-white px-4 py-2 flex items-center gap-2">
        <span>💬</span>
        <span className="font-semibold">Чат с мастером</span>
        <span className="text-xs opacity-75 ml-auto">Заявка #{orderId}</span>
      </div>

      {/* Область сообщений */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <p>💬 Напишите первое сообщение</p>
            <p className="text-xs mt-2">Задайте вопрос или уточните детали</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.senderRole === currentUserRole ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[70%] rounded-lg p-2 ${
                msg.senderRole === currentUserRole 
                  ? 'bg-primary text-white' 
                  : 'bg-white border shadow-sm'
              }`}>
                <div className="flex items-center gap-1 text-xs mb-1">
                  <span className={`inline-block w-5 h-5 rounded-full flex items-center justify-center text-xs ${getSenderBadge(msg.senderRole)}`}>
                    {getSenderIcon(msg.senderRole)}
                  </span>
                  <span className="font-medium">{msg.sender}</span>
                  <span className={`text-xs ${msg.senderRole === currentUserRole ? 'text-blue-200' : 'text-gray-400'}`}>
                    {msg.timestamp}
                  </span>
                </div>
                <div className="text-sm break-words">{msg.text}</div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Поле ввода */}
      <div className="border-t p-3 flex gap-2 bg-white">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Введите сообщение..."
          className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <button
          onClick={sendMessage}
          disabled={!newMessage.trim()}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition disabled:opacity-50"
        >
          📤 Отправить
        </button>
      </div>
    </div>
  );
};

export default OrderChat;