import { CheckCircle } from 'lucide-react';

interface CheckInSectionProps {
  onCheckin: () => void;
}

export function CheckInSection({ onCheckin }: CheckInSectionProps) {
  return (
    <div className="checkin-action fade-in">
      <button className="btn-primary btn-gradient btn-circle" onClick={onCheckin}>
        <CheckCircle size={48} strokeWidth={2.5} />
        <span style={{ fontSize: '18px', fontWeight: 800, marginTop: '4px' }}>I'm Good</span>
      </button>
    </div>
  );
}
