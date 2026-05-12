import { useState } from 'react';

interface StarRatingProps {
  rating: number;
  onRate: (rating: number) => void;
  readonly?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const StarRating = ({ rating, onRate, readonly = false, size = 'md' }: StarRatingProps) => {
  const [hover, setHover] = useState(0);

  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-xl',
    lg: 'text-3xl'
  };

  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={readonly}
          onClick={() => !readonly && onRate(star)}
          onMouseEnter={() => !readonly && setHover(star)}
          onMouseLeave={() => !readonly && setHover(0)}
          className={`focus:outline-none ${sizeClasses[size]} ${readonly ? 'cursor-default' : 'cursor-pointer'}`}
        >
          <span className={star <= (hover || rating) ? 'text-yellow-500' : 'text-gray-300'}>
            ★
          </span>
        </button>
      ))}
    </div>
  );
};

export default StarRating;