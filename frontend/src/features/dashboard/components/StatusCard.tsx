import { StatusBadge } from '../../../components/ui';
import { formatDate } from '../../../utils/date';
import type { StatusResponse } from '../../../types';

interface StatusCardProps {
  status: StatusResponse | null;
}

export function StatusCard({ status }: StatusCardProps) {
  return (
    <div className={`status-card ${status ? `status-card-${status.status.toLowerCase().replace('_', '-')}` : ''}`}>
      <div className="status-header">
        <h2 
          className={status ? `status-text-${status.status.toLowerCase().replace('_', '-')}` : ''}
          style={{ fontSize: '18px', fontWeight: 700 }}
        >
          Current Status
        </h2>
        {status && <StatusBadge status={status.status} />}
      </div>
      
      <div className="status-metrics">
        <div className="metric">
          <span className="metric-label">Last Check-In</span>
          <span className="metric-value">
            {formatDate(status?.last_checkin).time}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            {formatDate(status?.last_checkin).date}
          </span>
        </div>
        <div className="metric">
          <span className="metric-label">Due In</span>
          <span className="metric-value" style={{ color: (status?.hours_until_due || 0) < 0 ? 'var(--error)' : 'inherit' }}>
            {status ? `${Math.abs(status.hours_until_due).toFixed(1)}h` : '--h'}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            {(status?.hours_until_due || 0) < 0 ? 'OVERDUE' : 'Remaining'}
          </span>
        </div>
      </div>
    </div>
  );
}
