import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import type { StatusResponse, User } from '../types';

export function useStatus(user: User | null) {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [isLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    if (!user) return;
    try {
      const data = await api.getStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to fetch status', err);
    }
  }, [user]);

  const handleCheckin = async () => {
    if (!status) return;
    
    // Optimistic update
    const now = new Date().toISOString();
    const prevStatus = status;
    
    setStatus({
      ...status,
      status: 'SAFE',
      last_checkin: now,
      hours_until_due: status.interval_hours,
    });
    
    try {
      const res = await api.checkin();
      setStatus({
        ...status,
        status: res.status,
        last_checkin: res.timestamp,
        hours_until_due: res.hours_until_due,
      });
    } catch (err) {
      console.error('Check-in failed', err);
      setStatus(prevStatus); // Rollback
    }
  };

  useEffect(() => {
    // 1. Handle message from Service Worker
    const handleMessage = (event: MessageEvent) => {
      if (event.data && event.data.type === 'TRIGGER_CHECKIN') {
        console.log('[useStatus] Received TRIGGER_CHECKIN from SW');
        handleCheckin();
      }
    };

    // 2. Handle URL parameter (if app was opened fresh from notification)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'checkin' && user) {
      console.log('[useStatus] URL action=checkin detected');
      handleCheckin();
      // Clean up URL
      window.history.replaceState({}, document.title, "/");
    }

    navigator.serviceWorker?.addEventListener('message', handleMessage);
    return () => navigator.serviceWorker?.removeEventListener('message', handleMessage);
  }, [user, handleCheckin]);

  useEffect(() => {
    let interval: number;
    if (user) {
      fetchStatus();
      interval = window.setInterval(fetchStatus, 1*60*60*1000); // Poll every hour
    }
    return () => clearInterval(interval);
  }, [user, fetchStatus]);

  return {
    status,
    isLoading,
    fetchStatus,
    handleCheckin
  };
}
