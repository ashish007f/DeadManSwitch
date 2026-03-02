/**
 * Global constants for the frontend application.
 */

export const APP_NAME = "I'mGood";

export const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  SHOW_ONBOARDING: 'show_onboarding',
};

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
};

export const AUTH_STEPS = {
  PHONE: 'phone',
  OTP: 'otp',
  PROFILE: 'profile',
} as const;
