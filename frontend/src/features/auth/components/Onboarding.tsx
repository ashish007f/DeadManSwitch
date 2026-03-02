import { ArrowRight, Clock, Users, FileText, CheckCircle } from 'lucide-react';

export function Onboarding({ onComplete }: { onComplete: () => void }) {
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
              <p>Store helpful directions that only gets shared in an emergency.</p>
            </div>
          </div>
        </div>

        <button 
          className="btn-checkin" 
          style={{ marginTop: '32px' }}
          onClick={onComplete}
        >
          Get Started <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
}
