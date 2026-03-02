import { initializeApp } from 'firebase/app';
import { getAuth, RecaptchaVerifier } from 'firebase/auth';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

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

try {
  if (!firebaseConfig.apiKey) {
    throw new Error('Firebase API Key is missing. Check your environment variables.');
  }
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  
  // Language for OTP SMS
  auth.useDeviceLanguage();

  try {
    messaging = getMessaging(app);
  } catch (err) {
    console.warn('Firebase Messaging not supported in this browser:', err);
  }
} catch (err) {
  console.error('Failed to initialize Firebase:', err);
}

export { auth, messaging };

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
    const currentToken = await getToken(messaging, {
      vapidKey: import.meta.env.VITE_FIREBASE_VAPID_KEY,
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
