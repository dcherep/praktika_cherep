import { useState } from 'react';

interface BookingCalendarProps {
  onSelectDateTime: (date: string, time: string) => void;
  bookedSlots?: string[];
}

const BookingCalendar = ({ onSelectDateTime, bookedSlots = [] }: BookingCalendarProps) => {
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');

  const getDates = () => {
    const dates = [];
    for (let i = 0; i < 14; i++) {
      const d = new Date();
      d.setDate(d.getDate() + i);
      dates.push(d);
    }
    return dates;
  };

  const timeSlots = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'];

  const isSlotBooked = (date: string, time: string) => {
    return bookedSlots.includes(`${date}_${time}`);
  };

  const handleTimeSelect = (time: string) => {
    setSelectedTime(time);
    if (selectedDate && time) {
      onSelectDateTime(selectedDate, time);
    }
  };

  const dates = getDates();

  return (
    <div className="border rounded-xl p-4 bg-white shadow-sm">
      <h3 className="font-semibold text-primary-dark mb-3 flex items-center gap-2">
        <span>📅</span> Выберите дату и время
      </h3>

      {/* Календарь дат */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-2">Дата:</div>
        <div className="grid grid-cols-7 gap-1">
          {dates.map((date) => {
            const dateStr = date.toISOString().split('T')[0];
            const isSelected = selectedDate === dateStr;
            const dayName = date.toLocaleDateString('ru', { weekday: 'short' });
            const dayNum = date.getDate();
            const month = date.toLocaleDateString('ru', { month: 'short' });

            return (
              <button
                key={dateStr}
                onClick={() => {
                  setSelectedDate(dateStr);
                  setSelectedTime('');
                }}
                className={`p-2 rounded-lg text-center text-sm transition ${
                  isSelected
                    ? 'bg-primary text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                <div className="text-xs">{dayName}</div>
                <div className="font-bold text-base">{dayNum}</div>
                <div className="text-xs opacity-75">{month}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Выбор времени */}
      {selectedDate && (
        <div className="mb-4">
          <div className="text-sm text-gray-600 mb-2">Время:</div>
          <div className="grid grid-cols-4 gap-2">
            {timeSlots.map((time) => {
              const isBooked = isSlotBooked(selectedDate, time);
              const isSelected = selectedTime === time;
              return (
                <button
                  key={time}
                  onClick={() => !isBooked && handleTimeSelect(time)}
                  disabled={isBooked}
                  className={`p-2 rounded-lg text-sm transition ${
                    isSelected
                      ? 'bg-green-500 text-white'
                      : isBooked
                      ? 'bg-gray-200 text-gray-400 line-through cursor-not-allowed'
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  {time}
                  {isBooked && <span className="block text-xs">🔴 занято</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Отображение выбранного (без кнопки!) */}
      {selectedDate && selectedTime && (
        <div className="mt-4 p-2 bg-green-100 text-green-700 text-sm rounded-lg text-center">
          ✅ Выбрано: {selectedDate} в {selectedTime}
        </div>
      )}

      <div className="mt-4 text-xs text-gray-400 text-center border-t pt-3">
        🟢 свободно | 🔴 занято | выберите дату и время
      </div>
    </div>
  );
};

export default BookingCalendar;