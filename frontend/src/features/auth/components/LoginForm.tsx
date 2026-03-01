import { useRef } from 'react';
import { CheckCircle, Phone, ArrowRight } from 'lucide-react';
import { Spinner } from '../../../components/ui';

interface LoginFormProps {
  authStep: 'phone' | 'otp';
  phoneInput: string;
  setPhoneInput: (val: string) => void;
  otpInput: string[];
  setOtpInput: (val: string[]) => void;
  authError: string;
  authLoading: boolean;
  onSendOtp: () => void;
  onVerifyOtp: (code?: string) => void;
  onBackToPhone: () => void;
}

export function LoginForm({
  authStep,
  phoneInput,
  setPhoneInput,
  otpInput,
  setOtpInput,
  authError,
  authLoading,
  onSendOtp,
  onVerifyOtp,
  onBackToPhone,
}: LoginFormProps) {
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otpInput];
    newOtp[index] = value.slice(-1);
    setOtpInput(newOtp);
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
    if (newOtp.every(v => v !== '') && newOtp.join('').length === 6) {
      onVerifyOtp(newOtp.join(''));
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otpInput[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

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
            <button className="btn-checkin" onClick={onSendOtp} disabled={authLoading}>
              {authLoading ? <Spinner /> : (
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
            <button className="logout-btn" onClick={onBackToPhone} style={{ marginBottom: '20px', display: 'inline-block' }}>
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
              onClick={() => onVerifyOtp()}
              disabled={authLoading || otpInput.join('').length < 6}
            >
              {authLoading ? <Spinner /> : 'Verify Code'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
