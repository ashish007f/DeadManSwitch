import { useState } from 'react';
import { Settings as SettingsIcon, ChevronRight } from 'lucide-react';

// Hooks
import { useAuth } from './hooks/useAuth';
import { useStatus } from './hooks/useStatus';

// Components
import { Spinner } from './components/ui';
import { Header } from './components/shared/Header';
import { Onboarding } from './features/auth/components/Onboarding';
import { LoginForm } from './features/auth/components/LoginForm';
import { ProfileForm } from './features/auth/components/ProfileForm';
import { StatusCard } from './features/dashboard/components/StatusCard';
import { CheckInSection } from './features/dashboard/components/CheckInSection';
import { SettingsPanel } from './features/settings/components/SettingsPanel';

import './App.css';

export default function App() {
  const {
    user,
    loading,
    showOnboarding,
    setShowOnboarding,
    authStep,
    setAuthStep,
    phoneInput,
    setPhoneInput,
    otpInput,
    setOtpInput,
    displayNameInput,
    setDisplayNameInput,
    authError,
    authLoading,
    handleSendOtp,
    handleVerifyOtp,
    handleProfileSubmit,
    handleLogout
  } = useAuth();

  const { status, handleCheckin } = useStatus(user);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // 1. Loading State
  if (loading) {
    return (
      <div className="full-screen-center">
        <Spinner size={40} />
      </div>
    );
  }

  // 2. Onboarding
  if (!user && showOnboarding) {
    return <Onboarding onComplete={() => setShowOnboarding(false)} />;
  }

  // 3. Authentication (Login / OTP / Profile)
  if (!user) {
    if (authStep === 'profile') {
      return (
        <ProfileForm 
          displayNameInput={displayNameInput}
          setDisplayNameInput={setDisplayNameInput}
          authError={authError}
          authLoading={authLoading}
          onProfileSubmit={handleProfileSubmit}
        />
      );
    }
    
    return (
      <LoginForm 
        authStep={authStep}
        phoneInput={phoneInput}
        setPhoneInput={setPhoneInput}
        otpInput={otpInput}
        setOtpInput={setOtpInput}
        authError={authError}
        authLoading={authLoading}
        onSendOtp={handleSendOtp}
        onVerifyOtp={handleVerifyOtp}
        onBackToPhone={() => setAuthStep('phone')}
      />
    );
  }

  // 4. Main Application Dashboard
  return (
    <div className="app-container">
      <Header user={user} onLogout={handleLogout} />

      <main>
        <StatusCard status={status} />
        
        <CheckInSection onCheckin={handleCheckin} />

        <section className="settings-section">
          <div className="section-header">
            <h2 className="section-title">Settings</h2>
          </div>

          {isSettingsOpen ? (
            <SettingsPanel 
              onClose={() => setIsSettingsOpen(false)} 
              onSaveSuccess={() => setIsSettingsOpen(false)} 
            />
          ) : (
            <div 
              className="form-card settings-toggle" 
              onClick={() => setIsSettingsOpen(true)}
            >
              <div className="settings-toggle-content">
                <div className="settings-icon-wrapper">
                  <SettingsIcon size={20} color="var(--primary)" />
                </div>
                <div>
                  <div className="settings-label">Configure Notifications</div>
                  <div className="settings-sublabel">Interval, contacts, and instructions</div>
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
