import { StatusBadge } from '../../../components/ui';
import { formatDate } from '../../../utils/date';
import type { StatusResponse } from '../../../types';

interface StatusCardProps {
  status: StatusResponse | null;
}

export function StatusCard({ status }: StatusCardProps) {
  const statusType = status?.status || 'SAFE';
  let statusClass = 'safe';
  let statusTitle = "You're all set";
  
  if (statusType === 'DUE_SOON') {
    statusClass = 'due-soon';
    statusTitle = "Almost check-in time";
  } else if (statusType !== 'SAFE') {
    statusClass = 'danger';
    statusTitle = "Action Required";
  }
  
  return (
    <div className={`card status-card ${statusClass} fade-in`}>
      <div className="status-header">
        <h2>{statusTitle}</h2>
        {status && <StatusBadge status={statusType} />}
      </div>
      
      <div className="metrics-grid">
        <div className="metric-item">
          <span className="metric-label">Last Check-In</span>
          <span className="metric-value">
            {formatDate(status?.last_checkin).time}
          </span>
          <p style={{ fontSize: '10px' }}>
            {formatDate(status?.last_checkin).date}
          </p>
        </div>
        <div className="metric-item">
          <span className="metric-label">Next Due</span>
          <span className="metric-value" style={{ color: statusClass === 'danger' ? 'var(--error)' : 'inherit' }}>
            {status ? `${Math.abs(status.hours_until_due).toFixed(1)}h` : '--h'}
          </span>
          <p style={{ fontSize: '10px' }}>
            {status?.hours_until_due && status.hours_until_due < 0 ? 'OVERDUE' : 'Remaining'}
          </p>
        </div>
      </div>
    </div>
  );
}
