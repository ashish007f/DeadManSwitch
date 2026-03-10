import { useRef } from 'react';
import { Phone, ArrowRight, ArrowLeft } from 'lucide-react';
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
  onBack: () => void;
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
  onBack,
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
    <div className="auth-container">
      <div id="recaptcha-container"></div>
      <div className="card fade-in" style={{ textAlign: 'center' }}>
        <div className="hero-icon indigo" style={{ margin: '0 auto 24px' }}>
          <img src="/icon.svg" alt="logo" style={{ width: '32px', height: '32px' }} />
        </div>
        <h1>I'mGood</h1>
        <p style={{ marginTop: '8px', marginBottom: '32px' }}>
          Peace of mind with every check-in.
        </p>

        {authError && (
          <div style={{ background: '#fee2e2', color: '#ef4444', padding: '12px', borderRadius: '12px', marginBottom: '20px', fontSize: '13px', fontWeight: 500 }}>
            {authError}
          </div>
        )}

        {authStep === 'phone' && (
          <div>
            <div className="form-group">
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
              <p style={{ fontSize: '11px', marginTop: '8px', color: 'var(--text-muted)' }}>
                Include country code (e.g. +91)
              </p>
            </div>
            <button className="btn-primary btn-gradient" onClick={onSendOtp} disabled={authLoading}>
              {authLoading ? <Spinner /> : (
                <>Send Code <ArrowRight size={20} /></>
              )}
            </button>
            <button className="btn-secondary" onClick={onBack} style={{ marginTop: '16px' }}>
              <ArrowLeft size={18} /> Learn more about I'mGood
            </button>
          </div>
        )}

        {authStep === 'otp' && (
          <div>
            <p style={{ fontSize: '14px', marginBottom: '16px' }}>
              Code sent to <strong>{phoneInput}</strong>
            </p>
            <div className="otp-container">
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
              className="btn-primary btn-gradient" 
              onClick={() => onVerifyOtp()}
              disabled={authLoading || otpInput.join('').length < 6}
            >
              {authLoading ? <Spinner /> : 'Verify Code'}
            </button>
            <button className="btn-secondary" onClick={onBackToPhone} style={{ marginTop: '16px' }}>
              Change number
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
