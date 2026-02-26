export type CheckInStatus = 'SAFE' | 'DUE_SOON' | 'MISSED' | 'GRACE_PERIOD' | 'NOTIFIED';

export interface User {
  phone: string;
  display_name?: string;
  access_token?: string;
  refresh_token?: string;
}

export interface StatusResponse {
  status: CheckInStatus;
  last_checkin: string | null;
  hours_until_due: number;
  interval_hours: number;
}

export interface CheckInResponse {
  timestamp: string;
  status: CheckInStatus;
  hours_until_due: number;
}

export interface SettingsResponse {
  checkin_interval_hours: number;
  missed_buffer_hours: number;
  grace_period_hours: number;
  contacts: string[];
}

export interface InstructionsResponse {
  content: string;
}
