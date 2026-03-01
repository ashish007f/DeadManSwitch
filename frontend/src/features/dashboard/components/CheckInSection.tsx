import { MapPin } from 'lucide-react';

interface CheckInSectionProps {
  onCheckin: () => void;
}

export function CheckInSection({ onCheckin }: CheckInSectionProps) {
  return (
    <section className="checkin-section">
      <button className="btn-checkin" onClick={onCheckin}>
        <MapPin size={24} />
        Check In Now
      </button>
    </section>
  );
}
