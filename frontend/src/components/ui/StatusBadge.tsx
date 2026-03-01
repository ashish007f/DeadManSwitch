import type { CheckInStatus } from '../../types';

interface StatusBadgeProps {
  status: CheckInStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const labels: Record<CheckInStatus, string> = {
    SAFE: 'Safe',
    DUE_SOON: 'Due Soon',
    MISSED: 'Overdue',
    GRACE_PERIOD: 'Contacts Alerted',
    NOTIFIED: 'Emergency Triggered'
  };
  
  return (
    <div className={`status-badge ${status.toLowerCase().replace('_', '-')}`}>
      {labels[status] || status}
    </div>
  );
}
