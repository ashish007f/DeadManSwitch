import { useState } from 'react';
import type { TouchEvent } from 'react';

interface SwipeHandlers {
  onLeftSwipe?: () => void;
  onRightSwipe?: () => void;
  minDistance?: number;
}

export function useSwipe({ onLeftSwipe, onRightSwipe, minDistance = 50 }: SwipeHandlers) {
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);

  const onTouchStart = (e: TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minDistance;
    const isRightSwipe = distance < -minDistance;

    if (isLeftSwipe && onLeftSwipe) {
      onLeftSwipe();
    }
    
    if (isRightSwipe && onRightSwipe) {
      onRightSwipe();
    }
  };

  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd
  };
}
