import React, { useState, useEffect } from 'react';
import { Download, X } from 'lucide-react';
import { usePWAInstall } from '../../hooks/usePWAInstall';

export const InstallPrompt: React.FC = () => {
  const { isInstallable, isInstalled, handleInstallClick } = usePWAInstall();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Only show if installable, not already installed, and hasn't been dismissed in this session
    const isDismissed = sessionStorage.getItem('pwa-prompt-dismissed');
    if (isInstallable && !isInstalled && !isDismissed) {
      // Small delay to make it feel more natural
      const timer = setTimeout(() => setIsVisible(true), 2000);
      return () => clearTimeout(timer);
    }
  }, [isInstallable, isInstalled]);

  const handleDismiss = () => {
    setIsVisible(false);
    sessionStorage.setItem('pwa-prompt-dismissed', 'true');
  };

  const onInstall = async () => {
    await handleInstallClick();
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="install-prompt-banner fade-in">
      <div className="install-prompt-content">
        <div className="install-prompt-icon">
          <Download size={20} />
        </div>
        <div className="install-prompt-text">
          <p className="install-prompt-title">Install I'mGood</p>
          <p className="install-prompt-subtitle">Add to home screen for quick access and notifications.</p>
        </div>
      </div>
      <div className="install-prompt-actions">
        <button className="btn btn-primary btn-sm" onClick={onInstall}>
          Install
        </button>
        <button className="btn-icon" onClick={handleDismiss} aria-label="Dismiss">
          <X size={20} />
        </button>
      </div>
    </div>
  );
};
