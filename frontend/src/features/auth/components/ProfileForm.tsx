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
    <div className="login-container">
      <div className="auth-card">
        <div className="auth-icon">
          <CheckCircle size={40} color="var(--success)" />
        </div>
        <h1>I'mGood</h1>
        <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
          Final Step: Let's set up your profile.
        </p>

        {authError && <div className="alert alert-error">{authError}</div>}

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
            onClick={onProfileSubmit}
            disabled={authLoading}
          >
            {authLoading ? <Spinner /> : 'Get Started'}
          </button>
        </div>
      </div>
    </div>
  );
}
