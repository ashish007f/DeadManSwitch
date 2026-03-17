import { initializeApp } from 'firebase/app';
import { getAuth, RecaptchaVerifier } from 'firebase/auth';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';
import { initializeAppCheck, ReCaptchaV3Provider } from 'firebase/app-check';

// Replace these with your actual Firebase config
// or use environment variables in Vite (.env.local)
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};

let app: any = null;
let auth: any = null;
let messaging: any = null;
let appCheck: any = null;

try {
  if (!firebaseConfig.apiKey) {
    throw new Error('Firebase API Key is missing. Check your environment variables.');
  }
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  
  // Initialize App Check
  // Note: VITE_RECAPTCHA_V3_SITE_KEY should be added to .env
  const siteKey = import.meta.env.VITE_RECAPTCHA_V3_SITE_KEY || 'RECAPTCHA_V3_SITE_KEY_PLACEHOLDER';
  const enforceAppCheck = import.meta.env.ENFORCE_APP_CHECK === 'true';
  
  if (typeof window !== 'undefined' && enforceAppCheck) {
    // Enable debug token for local testing
    if (import.meta.env.DEV || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      (self as any).FIREBASE_APPCHECK_DEBUG_TOKEN = true;
    }

    try {
      appCheck = initializeAppCheck(app, {
        provider: new ReCaptchaV3Provider(siteKey),
        isTokenAutoRefreshEnabled: true
      });
      console.log('✓ Firebase App Check initialized');
    } catch (acErr) {
      console.warn('⚠ App Check failed to initialize (Expected on mobile IP):', acErr);
    }
  }

  // Language for OTP SMS
  auth.useDeviceLanguage();

  try {
    // VitePWA generates sw.js in the root of the output directory
    messaging = getMessaging(app);
  } catch (err) {
    console.warn('Firebase Messaging not supported in this browser:', err);
  }
} catch (err) {
  console.error('Failed to initialize Firebase:', err);
}

export { auth, messaging, appCheck };

export const setupRecaptcha = (elementId: string) => {
  if (!auth) return null;
  return new RecaptchaVerifier(auth, elementId, {
    size: 'invisible',
    callback: () => {
      // reCAPTCHA solved, allow signInWithPhoneNumber.
    }
  });
};

export const requestForToken = async () => {
  if (!messaging) return null;
  try {
    console.log('Current Permission:', Notification.permission);
    console.log('Is Secure Context:', window.isSecureContext);
    
    let permission = Notification.permission;
    
    if (permission === 'default') {
      try {
        permission = await Notification.requestPermission();
      } catch (e) {
        // Fallback for older browsers
        permission = await new Promise((resolve) => {
          Notification.requestPermission((p) => resolve(p));
        });
      }
    }
    
    console.log('Notification permission status:', permission);
    
    if (permission !== 'granted') {
      return null;
    }

    // 2. Check Service Worker
    if (!navigator.serviceWorker) {
      console.warn('Service Worker not supported or insecure origin.');
      return null;
    }

    // 3. Get Registration and Token
    const registration = await navigator.serviceWorker.getRegistration();
    const vapidKey = import.meta.env.VITE_FIREBASE_VAPID_KEY;
    
    if (!vapidKey) {
      console.error('VITE_FIREBASE_VAPID_KEY is missing!');
      return null;
    }

    const currentToken = await getToken(messaging, {
      vapidKey: vapidKey,
      serviceWorkerRegistration: registration
    });
    
    if (currentToken) {
      return currentToken;
    } else {
      console.log('No registration token available. Request permission to generate one.');
    }
  } catch (err) {
    console.log('An error occurred while retrieving token. ', err);
  }
  return null;
};

export const onMessageListener = () =>
  new Promise((resolve) => {
    if (!messaging) return;
    onMessage(messaging, (payload) => {
      resolve(payload);
    });
  });
