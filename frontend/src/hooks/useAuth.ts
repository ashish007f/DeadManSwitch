import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  signInWithPhoneNumber, 
  RecaptchaVerifier,
} from 'firebase/auth';
import type { ConfirmationResult } from 'firebase/auth';
import { auth, requestForToken, onMessageListener } from '../lib/firebase';
import { api } from '../api';
import type { User } from '../types';
import { STORAGE_KEYS, AUTH_STEPS } from '../constants';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(true);
  
  const [authStep, setAuthStep] = useState<typeof AUTH_STEPS[keyof typeof AUTH_STEPS]>(AUTH_STEPS.PHONE);
  const [phoneInput, setPhoneInput] = useState('');
  const [otpInput, setOtpInput] = useState(['', '', '', '', '', '']);
  const [displayNameInput, setDisplayNameInput] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  
  const [confirmationResult, setConfirmationResult] = useState<ConfirmationResult | null>(null);
  const recaptchaVerifier = useRef<RecaptchaVerifier | null>(null);

  const checkAuth = useCallback(async () => {
    const hasToken = !!localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
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
  }, []);

  const handleLogout = async () => {
    try {
      await api.logout();
      setUser(null);
      setAuthStep(AUTH_STEPS.PHONE);
      setPhoneInput('');
      setOtpInput(['', '', '', '', '', '']);
    } catch (err) {
      console.error('Logout failed', err);
    }
  };

  const handleSendOtp = async () => {
    if (!phoneInput || phoneInput.length < 10) {
      setAuthError('Enter a valid phone number with country code (e.g. +91)');
      return;
    }
    
    setAuthLoading(true);
    setAuthError('');
    
    try {
      if (!recaptchaVerifier.current) {
        recaptchaVerifier.current = new RecaptchaVerifier(auth, 'recaptcha-container', {
          size: 'invisible'
        });
      }

      const result = await signInWithPhoneNumber(auth, phoneInput, recaptchaVerifier.current);
      setConfirmationResult(result);
      setAuthStep(AUTH_STEPS.OTP);
    } catch (err: any) {
      console.error(err);
      setAuthError(err.message || 'Failed to send code');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleVerifyOtp = async (code?: string) => {
    const finalCode = code || otpInput.join('');
    if (finalCode.length !== 6 || !confirmationResult) return;
    
    setAuthLoading(true);
    setAuthError('');
    try {
      const userCredential = await confirmationResult.confirm(finalCode);
      const idToken = await userCredential.user.getIdToken();
      const userData = await api.verifyFirebase(idToken);
      
      if (!userData.display_name || userData.display_name === userData.phone) {
        setAuthStep(AUTH_STEPS.PROFILE);
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
  };

  const handleProfileSubmit = async () => {
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
  };

  const handleFcmToken = useCallback(async () => {
    try {
      const token = await requestForToken();
      if (token) {
        await api.updateFcmToken(token);
      }
    } catch (err) {
      console.error('Failed to get FCM token', err);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (user) {
      handleFcmToken();
      onMessageListener().then(() => {
        // Handle foreground notification (e.g., update local state or show custom UI)
      });
    }
  }, [user, handleFcmToken]);

  return {
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
  };
}
