import { useState } from 'react';
import { Home, Settings as SettingsIcon, HelpCircle } from 'lucide-react';

// Hooks
import { useAuth } from './hooks/useAuth';
import { useStatus } from './hooks/useStatus';
import { useSwipe } from './hooks/useSwipe';
import { STORAGE_KEYS } from './constants';

// Components
import { Spinner, InstallPrompt } from './components/ui';
import { Header } from './components/shared/Header';
import { Onboarding } from './features/auth/components/Onboarding';
import { LoginForm } from './features/auth/components/LoginForm';
import { ProfileForm } from './features/auth/components/ProfileForm';
import { StatusCard } from './features/dashboard/components/StatusCard';
import { CheckInSection } from './features/dashboard/components/CheckInSection';
import { SettingsPanel } from './features/settings/components/SettingsPanel';
import { SupportPanel } from './features/support/components/SupportPanel';

import './App.css';

type Tab = 'home' | 'settings' | 'support';

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
  const [activeTab, setActiveTab] = useState<Tab>('home');

  // Global Swipe Logic
  const swipeHandlers = useSwipe({
    onRightSwipe: () => {
      if (!user && !showOnboarding && authStep === 'otp') {
        setAuthStep('phone');
      } else if (!user && !showOnboarding && authStep === 'phone') {
        setShowOnboarding(true);
      } else if (user) {
        if (activeTab === 'settings') setActiveTab('home');
        if (activeTab === 'support') setActiveTab('settings');
      }
    },
    onLeftSwipe: () => {
      if (user) {
        if (activeTab === 'home') setActiveTab('settings');
        if (activeTab === 'settings') setActiveTab('support');
      }
    }
  });

  if (loading) {
    return (
      <div className="full-center">
        <Spinner size={40} />
      </div>
    );
  }

  // 1. Onboarding Flow
  if (!user && showOnboarding) {
    return (
      <div className="global-gesture-wrapper" {...swipeHandlers}>
        <Onboarding 
          onComplete={() => {
            localStorage.setItem(STORAGE_KEYS.SHOW_ONBOARDING, 'false');
            setShowOnboarding(false);
          }} 
        />
        <InstallPrompt />
      </div>
    );
  }

  // 2. Auth Flow
  if (!user) {
    return (
      <div className="global-gesture-wrapper" {...swipeHandlers}>
        {authStep === 'profile' ? (
          <ProfileForm 
            displayNameInput={displayNameInput}
            setDisplayNameInput={setDisplayNameInput}
            authError={authError}
            authLoading={authLoading}
            onProfileSubmit={handleProfileSubmit}
          />
        ) : (
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
            onBack={() => setShowOnboarding(true)}
          />
        )}
        <InstallPrompt />
      </div>
    );
  }

  // 3. Main Dashboard Flow
  return (
    <div className="global-gesture-wrapper" {...swipeHandlers}>
      <div className="app-container">
        <Header user={user} onLogout={handleLogout} />

        <main style={{ flex: 1 }}>
          {activeTab === 'home' && (
            <div className="fade-in">
              <StatusCard status={status} />
              <CheckInSection onCheckin={handleCheckin} />
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="fade-in">
              <h2 style={{ marginBottom: '20px' }}>Settings</h2>
              <SettingsPanel 
                onClose={() => setActiveTab('home')} 
                onSaveSuccess={() => setActiveTab('home')} 
              />
            </div>
          )}

          {activeTab === 'support' && (
            <SupportPanel />
          )}
        </main>

        <InstallPrompt />

        {/* Bottom Navigation */}
        <nav className="bottom-nav">
          <button 
            className={`nav-btn ${activeTab === 'home' ? 'active' : ''}`}
            onClick={() => setActiveTab('home')}
          >
            <Home size={24} />
            <span>Home</span>
          </button>
          <button 
            className={`nav-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <SettingsIcon size={24} />
            <span>Settings</span>
          </button>
          <button 
            className={`nav-btn ${activeTab === 'support' ? 'active' : ''}`}
            onClick={() => setActiveTab('support')}
          >
            <HelpCircle size={24} />
            <span>Support</span>
          </button>
        </nav>
      </div>
    </div>
  );
}
