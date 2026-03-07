import { CheckCircle, User as UserIcon } from 'lucide-react';
import { Spinner } from '../../../components/ui';

interface ProfileFormProps {
  displayNameInput: string;
  setDisplayNameInput: (val: string) => void;
  authError: string;
  authLoading: boolean;
  onProfileSubmit: () => void;
}

export function ProfileForm({
  displayNameInput,
  setDisplayNameInput,
  authError,
  authLoading,
  onProfileSubmit,
}: ProfileFormProps) {
  return (
    <div className="auth-container">
      <div className="card fade-in" style={{ textAlign: 'center' }}>
        <div className="hero-icon indigo" style={{ margin: '0 auto 24px' }}>
          <img src="/icon.svg" alt="logo" style={{ width: '32px', height: '32px' }} />
        </div>
        <h1>I'mGood</h1>
        <p style={{ marginTop: '8px', marginBottom: '32px' }}>
          Complete your profile to get started.
        </p>

        {authError && (
          <div style={{ background: '#fee2e2', color: '#ef4444', padding: '12px', borderRadius: '12px', marginBottom: '20px', fontSize: '13px' }}>
            {authError}
          </div>
        )}

        <div className="form-group">
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
          className="btn-primary btn-gradient" 
          onClick={onProfileSubmit}
          disabled={authLoading}
        >
          {authLoading ? <Spinner /> : 'Get Started'}
        </button>
      </div>
    </div>
  );
}
