import { useState, useEffect, useRef } from 'react';
import { 
  LogOut, 
  MapPin, 
  Settings as SettingsIcon, 
  ChevronRight, 
  Check, 
  CheckCircle,
  User as UserIcon,
  Phone,
  ArrowRight,
  Clock,
  Users,
  FileText
} from 'lucide-react';
import { 
  signInWithPhoneNumber, 
  RecaptchaVerifier 
} from 'firebase/auth';
import type { 
  ConfirmationResult, 
} from 'firebase/auth';
import { auth, requestForToken, onMessageListener } from './firebase';
import { api } from './api';
import type { 
  User, 
  StatusResponse, 
  SettingsResponse, 
  CheckInStatus 
} from './types';
import './App.css';

// --- Sub-components ---

function formatDate(dateString: string | null | undefined) {
  if (!dateString) return { time: '--:--', date: 'Never' };
  
  // Ensure the date string is treated as UTC by appending 'Z' if missing
  const utcString = dateString.endsWith('Z') ? dateString : `${dateString}Z`;
  const date = new Date(utcString);
  
  return {
    time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    date: date.toLocaleDateString()
  };
}

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
  const [showOnboarding, setShowOnboarding] = useState(true);
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
    if (user) {
      handleFcmToken();
      onMessageListener().then((payload) => {
        console.log('Foreground message received:', payload);
        // You could show a toast or alert here
        alert('Notification: ' + (payload as any)?.notification?.title);
      });
    }
  }, [user]);

  useEffect(() => {
    let interval: number;
    if (user) {
      fetchStatus();
      interval = window.setInterval(fetchStatus, 60000); // Refresh every 1 min to keep status updated
    }
    return () => clearInterval(interval);
  }, [user]);

  async function handleFcmToken() {
    try {
      const token = await requestForToken();
      if (token) {
        await api.updateFcmToken(token);
      }
    } catch (err) {
      console.error('Failed to get FCM token', err);
    }
  }

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

  if (!user && showOnboarding) {
    return (
      <div className="login-container">
        <div className="auth-card onboarding-card">
          <div className="auth-icon">
            <CheckCircle size={48} color="var(--success)" />
          </div>
          <h1 style={{ fontSize: '28px', marginBottom: '8px' }}>Welcome to I'mGood</h1>
          <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>
            A simple, reliable safety system for your peace of mind.
          </p>

          <div className="features-list">
            <div className="feature-item">
              <div className="feature-icon"><Clock size={20} /></div>
              <div className="feature-content">
                <h3>Quick Check-ins</h3>
                <p>Confirm you're safe with a single tap at scheduled intervals.</p>
              </div>
            </div>
            
            <div className="feature-item">
              <div className="feature-icon"><Users size={20} /></div>
              <div className="feature-content">
                <h3>Emergency Contacts</h3>
                <p>Trusted people get alerted only if you miss your check-in.</p>
              </div>
            </div>

            <div className="feature-item">
              <div className="feature-icon"><FileText size={20} /></div>
              <div className="feature-content">
                <h3>Secure Instructions</h3>
                <p>Store info /directions that only gets shared in an emergency.</p>
              </div>
            </div>
          </div>

          <button 
            className="btn-checkin" 
            style={{ marginTop: '32px' }}
            onClick={() => setShowOnboarding(false)}
          >
            Get Started <ArrowRight size={20} />
          </button>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="login-container">
        <div id="recaptcha-container"></div>
        <div className="auth-card">
          <div className="auth-icon">
            <CheckCircle size={40} color="var(--success)" />
          </div>
          <h1>I'mGood</h1>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
            Peace of mind with every check-in.
          </p>

          {authError && <div className="alert alert-error">{authError}</div>}

          {authStep === 'phone' && (
            <div className="auth-step">
              <div className="form-group" style={{ textAlign: 'left' }}>
                <label>Phone Number</label>
                <div style={{ position: 'relative' }}>
                  <Phone size={18} style={{ position: 'absolute', left: 14, top: 14, color: 'var(--text-muted)' }} />
                  <input 
                    type="tel" 
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
          <CheckCircle size={22} color="var(--primary)" style={{ flexShrink: 0 }} />
          <h1>I'mGood</h1>
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
          step="any"
          value={settings?.checkin_interval_hours ?? ''} 
          onChange={e => setSettings(s => s ? {...s, checkin_interval_hours: parseFloat(e.target.value) || 0} : null)}
        />
        <p className="form-hint">How often should you check in?</p>
      </div>

      <div className="form-group">
        <label>Missed Buffer (hours)</label>
        <input 
          type="number" 
          step="any"
          value={settings?.missed_buffer_hours ?? ''} 
          onChange={e => setSettings(s => s ? {...s, missed_buffer_hours: parseFloat(e.target.value) || 0} : null)}
        />
        <p className="form-hint">Extra time before the interval is considered MISSED.</p>
      </div>

      <div className="form-group">
        <label>Grace Period (hours)</label>
        <input 
          type="number" 
          step="any"
          value={settings?.grace_period_hours ?? ''} 
          onChange={e => setSettings(s => s ? {...s, grace_period_hours: parseFloat(e.target.value) || 0} : null)}
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
