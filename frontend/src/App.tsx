import { useState, useEffect, useRef } from 'react';
import { 
  LogOut, 
  MapPin, 
  Settings as SettingsIcon, 
  ChevronRight, 
  Shield, 
  Check, 
  User as UserIcon,
  Phone,
  ArrowRight
} from 'lucide-react';
import { 
  signInWithPhoneNumber, 
  RecaptchaVerifier 
} from 'firebase/auth';
import type { 
  ConfirmationResult, 
} from 'firebase/auth';
import { auth } from './firebase';
import { api } from './api';
import type { 
  User, 
  StatusResponse, 
  SettingsResponse, 
  CheckInStatus 
} from './types';
import './App.css';

// --- Sub-components ---

function StatusBadge({ status }: { status: CheckInStatus }) {
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

// --- Main App ---

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  
  // Auth steps: 'phone' | 'otp' | 'profile'
  const [authStep, setAuthStep] = useState<'phone' | 'otp' | 'profile'>('phone');
  const [phoneInput, setPhoneInput] = useState('');
  const [otpInput, setOtpInput] = useState(['', '', '', '', '', '']);
  const [displayNameInput, setDisplayNameInput] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  
  // Firebase Auth State
  const [confirmationResult, setConfirmationResult] = useState<ConfirmationResult | null>(null);
  const recaptchaVerifier = useRef<RecaptchaVerifier | null>(null);
  
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    let interval: number;
    if (user) {
      fetchStatus();
      interval = window.setInterval(fetchStatus, 5000);
    }
    return () => clearInterval(interval);
  }, [user]);

  async function checkAuth() {
    const hasToken = !!localStorage.getItem('refresh_token');
    if (!hasToken) {
      setLoading(false);
      return;
    }

    try {
      const data = await api.me();
      setUser(data);
    } catch (err) {
      console.error('Auth check failed', err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function fetchStatus() {
    try {
      const data = await api.getStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to fetch status', err);
    }
  }

  // --- Auth Handlers ---

  async function handleSendOtp() {
    if (!phoneInput || phoneInput.length < 10) {
      setAuthError('Enter a valid phone number with country code (e.g. +91)');
      return;
    }
    
    setAuthLoading(true);
    setAuthError('');
    
    try {
      // Setup Recaptcha if not exists
      if (!recaptchaVerifier.current) {
        recaptchaVerifier.current = new RecaptchaVerifier(auth, 'recaptcha-container', {
          size: 'invisible'
        });
      }

      const result = await signInWithPhoneNumber(auth, phoneInput, recaptchaVerifier.current);
      setConfirmationResult(result);
      setAuthStep('otp');
    } catch (err: any) {
      console.error(err);
      setAuthError(err.message || 'Failed to send code');
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleVerifyOtp(code?: string) {
    const finalCode = code || otpInput.join('');
    if (finalCode.length !== 6 || !confirmationResult) return;
    
    setAuthLoading(true);
    setAuthError('');
    try {
      const userCredential = await confirmationResult.confirm(finalCode);
      const idToken = await userCredential.user.getIdToken();

      const userData = await api.verifyFirebase(idToken);
      
      if (!userData.display_name || userData.display_name === userData.phone) {
        setAuthStep('profile');
      } else {
        setUser(userData);
      }
    } catch (err: any) {
      console.error(err);
      setAuthError('Invalid or expired code');
      setOtpInput(['', '', '', '', '', '']);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleProfileSubmit() {
    setAuthLoading(true);
    try {
      if (displayNameInput.trim()) {
        const userData = await api.updateDisplayName(displayNameInput.trim());
        setUser(userData);
      } else {
        const userData = await api.me();
        setUser(userData);
      }
    } catch (err: any) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await api.logout();
      setUser(null);
      setAuthStep('phone');
      setPhoneInput('');
      setOtpInput(['', '', '', '', '', '']);
    } catch (err) {
      console.error('Logout failed', err);
    }
  }

  // --- Check-in Handlers ---

  async function handleCheckin() {
    if (!status) return;
    
    // Optimistic update
    const now = new Date().toISOString();
    setStatus({
      ...status,
      status: 'SAFE',
      last_checkin: now,
      hours_until_due: status.interval_hours,
    });
    
    try {
      const res = await api.checkin();
      setStatus({
        ...status,
        status: res.status,
        last_checkin: res.timestamp,
        hours_until_due: res.hours_until_due,
      });
    } catch (err) {
      console.error('Check-in failed', err);
      fetchStatus(); // Rollback
    }
  }

  // --- OTP Input Helper ---
  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    
    const newOtp = [...otpInput];
    newOtp[index] = value.slice(-1);
    setOtpInput(newOtp);
    
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
    
    if (newOtp.every(v => v !== '') && newOtp.join('').length === 6) {
      handleVerifyOtp(newOtp.join(''));
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otpInput[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>
        <div className="spinner" style={{ borderTopColor: 'var(--primary)' }}></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="login-container">
        <div id="recaptcha-container"></div>
        <div className="auth-card">
          <div className="auth-icon">
            <Shield size={32} />
          </div>
          <h1>Dead Man Switch</h1>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
            Stay connected. Stay safe.
          </p>

          {authError && <div className="alert alert-error">{authError}</div>}

          {authStep === 'phone' && (
            <div className="auth-step">
              <div className="form-group" style={{ textAlign: 'left' }}>
                <label>Phone Number</label>
                <div style={{ position: 'relative' }}>
                  <Phone size={18} style={{ position: 'absolute', left: 14, top: 14, color: 'var(--text-muted)' }} />
                  <input 
                    type="mobile" 
                    placeholder="+919876543210" 
                    value={phoneInput}
                    onChange={e => setPhoneInput(e.target.value)}
                    style={{ paddingLeft: 44 }}
                  />
                </div>
                <p className="form-hint" style={{ marginTop: '8px' }}>Include country code (e.g. +91 for IND)</p>
              </div>
              <button 
                className="btn-checkin" 
                onClick={handleSendOtp}
                disabled={authLoading}
              >
                {authLoading ? <div className="spinner"></div> : (
                  <>Send Code <ArrowRight size={20} /></>
                )}
              </button>
            </div>
          )}

          {authStep === 'otp' && (
            <div className="auth-step">
              <p style={{ fontSize: '14px', marginBottom: '8px' }}>
                Code sent to <strong>{phoneInput}</strong>
              </p>
              <button 
                className="logout-btn" 
                onClick={() => setAuthStep('phone')}
                style={{ marginBottom: '20px', display: 'inline-block' }}
              >
                Change number
              </button>
              
              <div className="otp-inputs">
                {otpInput.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => { otpRefs.current[idx] = el; }}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    className="otp-input"
                    value={digit}
                    onChange={e => handleOtpChange(idx, e.target.value)}
                    onKeyDown={e => handleOtpKeyDown(idx, e)}
                  />
                ))}
              </div>
              
              <button 
                className="btn-checkin" 
                onClick={() => handleVerifyOtp()}
                disabled={authLoading || otpInput.join('').length < 6}
              >
                {authLoading ? <div className="spinner"></div> : 'Verify Code'}
              </button>
            </div>
          )}

          {authStep === 'profile' && (
            <div className="auth-step">
              <div className="form-group" style={{ textAlign: 'left' }}>
                <label>Display Name (Optional)</label>
                <div style={{ position: 'relative' }}>
                  <UserIcon size={18} style={{ position: 'absolute', left: 14, top: 14, color: 'var(--text-muted)' }} />
                  <input 
                    type="text" 
                    placeholder="What's your name?" 
                    value={displayNameInput}
                    onChange={e => setDisplayNameInput(e.target.value)}
                    style={{ paddingLeft: 44 }}
                  />
                </div>
              </div>
              <button 
                className="btn-checkin" 
                onClick={handleProfileSubmit}
                disabled={authLoading}
              >
                {authLoading ? <div className="spinner"></div> : 'Get Started'}
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="brand">
          <h1>🛡️ Dead Man Switch</h1>
        </div>
        <div className="user-profile">
          <div className="display-name">{user.display_name || user.phone}</div>
          <button className="logout-btn" onClick={handleLogout}>
            <LogOut size={12} style={{ marginRight: 4 }} /> Logout
          </button>
        </div>
      </header>

      <main>
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
                {status?.last_checkin ? new Date(status.last_checkin).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {status?.last_checkin ? new Date(status.last_checkin).toLocaleDateString() : 'Never'}
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

        <section className="checkin-section">
          <button className="btn-checkin" onClick={handleCheckin}>
            <MapPin size={24} />
            Check In Now
          </button>
        </section>

        <section className="settings-section">
          <div className="section-header">
            <h2 className="section-title">Settings</h2>
          </div>

          {isSettingsOpen && <SettingsPanel onClose={() => setIsSettingsOpen(false)} onSaveSuccess={() => setIsSettingsOpen(false)} />}
          
          {!isSettingsOpen && (
            <div className="form-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', opacity: 0.8 }} onClick={() => setIsSettingsOpen(true)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 40, height: 40, borderRadius: 12, background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <SettingsIcon size={20} color="var(--primary)" />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '14px' }}>Configure Notifications</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Interval, contacts, and instructions</div>
                </div>
              </div>
              <ChevronRight size={20} color="#cbd5e1" />
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

// --- Settings Panel ---

function SettingsPanel({ onClose, onSaveSuccess }: { onClose: () => void, onSaveSuccess: () => void }) {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [instructions, setInstructions] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [sData, iData] = await Promise.all([
        api.getSettings(),
        api.getInstructions()
      ]);
      setSettings(sData);
      setInstructions(iData.content || '');
    } catch (err) {
      console.error('Failed to load settings', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!settings) return;
    setSaving(true);
    setSuccess(false);
    try {
      // Ensure we don't send NaN
      const settingsToSave = {
        ...settings,
        checkin_interval_hours: settings.checkin_interval_hours || 48,
        missed_buffer_hours: settings.missed_buffer_hours || 1,
        grace_period_hours: settings.grace_period_hours || 24,
      };

      await Promise.all([
        api.updateSettings(settingsToSave),
        api.saveInstructions(instructions)
      ]);
      setSuccess(true);
      // Collapse after a short delay so the user sees the success state
      setTimeout(() => {
        setSuccess(false);
        onSaveSuccess();
      }, 800);
    } catch (err) {
      console.error('Save failed', err);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}><div className="spinner" style={{ borderTopColor: 'var(--primary)', margin: '0 auto' }}></div></div>;

  return (
    <div className="form-card">
      <div className="form-group">
        <label>Check-In Interval (hours)</label>
        <input 
          type="number" 
          value={settings?.checkin_interval_hours || ''} 
          onChange={e => setSettings(s => s ? {...s, checkin_interval_hours: parseInt(e.target.value) || 0} : null)}
        />
        <p className="form-hint">How often should you check in?</p>
      </div>

      <div className="form-group">
        <label>Missed Buffer (hours)</label>
        <input 
          type="number" 
          value={settings?.missed_buffer_hours || ''} 
          onChange={e => setSettings(s => s ? {...s, missed_buffer_hours: parseInt(e.target.value) || 0} : null)}
        />
        <p className="form-hint">Extra time before the interval is considered MISSED.</p>
      </div>

      <div className="form-group">
        <label>Grace Period (hours)</label>
        <input 
          type="number" 
          value={settings?.grace_period_hours || ''} 
          onChange={e => setSettings(s => s ? {...s, grace_period_hours: parseInt(e.target.value) || 0} : null)}
        />
        <p className="form-hint">Extra time after MISSED before contacts get full instructions.</p>
      </div>

      <div className="form-group">
        <label>Trusted Contacts</label>
        <input 
          type="text" 
          placeholder="email or phone, comma separated"
          value={settings?.contacts?.join(', ') || ''} 
          onChange={e => setSettings(s => s ? {...s, contacts: e.target.value.split(',').map(c => c.trim()).filter(Boolean)} : null)}
        />
      </div>

      <div className="form-group">
        <label>Emergency Instructions</label>
        <textarea 
          rows={4}
          placeholder="Instructions for your contacts..."
          value={instructions}
          onChange={e => setInstructions(e.target.value)}
        />
        <p className="form-hint">These will be sent only when the grace period expires.</p>
      </div>

      <div className="form-actions">
        <button className="btn-secondary" onClick={onClose}>Close</button>
        <button className="btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? <div className="spinner" style={{ margin: '0 auto' }}></div> : (success ? <Check size={20} style={{ margin: '0 auto' }} /> : 'Save Changes')}
        </button>
      </div>
    </div>
  );
}

export default App;
