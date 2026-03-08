import { useState } from 'react';
import { 
  ArrowRight, 
  ArrowLeft,
  Clock, 
  Users, 
  Shield, 
  Bell
} from 'lucide-react';
import { useSwipe } from '../../../hooks/useSwipe';

interface OnboardingProps {
  onComplete: () => void;
}

// UI Version 0.1.3 - Perfectly Standardized
export function Onboarding({ onComplete }: OnboardingProps) {
  const [step, setStep] = useState(1);

  const { onTouchStart, onTouchMove, onTouchEnd } = useSwipe({
    onLeftSwipe: () => step === 1 && setStep(2),
    onRightSwipe: () => step === 2 && setStep(1),
  });

  return (
    <div 
      className="auth-container" 
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
    >
      <div className="card fade-in">
        
        {/* STEP 1: KEY FEATURES */}
        {step === 1 && (
          <div className="onboarding-step" style={{ textAlign: 'center' }}>
            <div className="hero-icon indigo" style={{ margin: '0 auto 24px' }}>
              <img src="/icon.svg" alt="logo" style={{ width: '32px', height: '32px' }} />
            </div>
            <h1>I'mGood</h1>
            <p style={{ marginTop: '8px', marginBottom: '32px' }}>
              Simple, secure, and reliable safety system.
            </p>

            <div className="list-vertical" style={{ textAlign: 'left' }}>
              <div className="list-item">
                <div className="list-item-icon"><Clock size={20} /></div>
                <div className="item-content">
                  <h3>Quick Check-ins</h3>
                  <p>Confirm you're safe with a single tap at scheduled intervals.</p>
                </div>
              </div>
              
              <div className="list-item">
                <div className="list-item-icon"><Users size={20} /></div>
                <div className="item-content">
                  <h3>Emergency Contacts</h3>
                  <p>Trusted people get alerted only if you miss your window.</p>
                </div>
              </div>

              <div className="list-item">
                <div className="list-item-icon"><Shield size={20} /></div>
                <div className="item-content">
                  <h3>Privacy First</h3>
                  <p>Your identity and instructions are AES-256 encrypted.</p>
                </div>
              </div>

              <div className="list-item">
                <div className="list-item-icon"><Bell size={20} /></div>
                <div className="item-content">
                  <h3>Smart Reminders</h3>
                  <p>Multiple notification layers ensure you never forget.</p>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '40px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button className="btn-primary btn-gradient" onClick={onComplete}>
                Get Started <ArrowRight size={20} />
              </button>
              <button className="btn-secondary" onClick={() => setStep(2)}>
                How it Works
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: HOW IT WORKS */}
        {step === 2 && (
          <div className="onboarding-step" style={{ textAlign: 'center' }}>
            <div className="hero-icon indigo" style={{ margin: '0 auto 24px' }}>
              <img src="/icon.svg" alt="logo" style={{ width: '32px', height: '32px' }} />
            </div>
            <h1>How it Works</h1>
            <p style={{ marginTop: '8px', marginBottom: '32px' }}>
              Simple daily safety for your peace of mind.
            </p>

            <div className="steps-container" style={{ textAlign: 'left' }}>
              <div className="step-row">
                <div className="step-dot">1</div>
                <div className="item-content">
                  <h3>Setup</h3>
                  <p>Set your interval and add trusted contacts.</p>
                </div>
              </div>
              <div className="step-line"></div>
              
              <div className="step-row">
                <div className="step-dot">2</div>
                <div className="item-content">
                  <h3>Check-in</h3>
                  <p>Tap "I'm Good" once a day (or your interval).</p>
                </div>
              </div>
              <div className="step-line"></div>
              
              <div className="step-row">
                <div className="step-dot">3</div>
                <div className="item-content">
                  <h3>Reminders</h3>
                  <p>We'll nudge you if you forget your check-in.</p>
                </div>
              </div>
              <div className="step-line"></div>
              
              <div className="step-row">
                <div className="step-dot">4</div>
                <div className="item-content">
                  <h3>Soft Alert</h3>
                  <p>Missed it? We gently notify your contacts.</p>
                </div>
              </div>
              <div className="step-line"></div>
              
              <div className="step-row">
                <div className="step-dot">5</div>
                <div className="item-content">
                  <h3>Emergency</h3>
                  <p>Still no word? We alert your contacts.</p>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '40px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button className="btn-primary btn-gradient" onClick={onComplete}>
                Get Started
              </button>
              <button className="btn-secondary" onClick={() => setStep(1)}>
                <ArrowLeft size={18} /> Back to Features
              </button>
            </div>
          </div>
        )}

        {/* PROGRESS INDICATOR */}
        <div style={{ marginTop: '32px', display: 'flex', gap: '8px', justifyContent: 'center' }}>
          {[1, 2].map(i => (
            <div 
              key={i} 
              style={{ 
                width: '8px', 
                height: '8px', 
                borderRadius: '50%', 
                background: i === step ? 'var(--primary)' : 'var(--border)',
                transition: 'all 0.3s'
              }} 
            />
          ))}
        </div>

      </div>
    </div>
  );
}
