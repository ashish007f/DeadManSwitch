import { useState, useEffect } from 'react';
import { api } from '../api';
import type { SettingsResponse } from '../types';

export function useSettings() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [instructions, setInstructions] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const loadSettings = async () => {
    try {
      const [sData, iData] = await Promise.all([
        api.getSettings(),
        api.getInstructions()
      ]);
      setSettings(sData);
      setInstructions(iData.content || '');
    } catch (err) {
      console.error('Failed to load settings', err);
    } finally {
      setIsLoading(false);
    }
  };

  const updateSettings = async () => {
    if (!settings) return;
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const settingsToSave = {
        ...settings,
        checkin_interval_hours: Number(settings.checkin_interval_hours) || 48,
        missed_buffer_hours: Number(settings.missed_buffer_hours) || 1,
        grace_period_hours: Number(settings.grace_period_hours) || 24,
        contacts: (settings.contacts || []).map(c => c.trim()).filter(Boolean),
      };

      await Promise.all([
        api.updateSettings(settingsToSave),
        api.saveInstructions(instructions)
      ]);
      setSaveSuccess(true);
      return true;
    } catch (err) {
      console.error('Save failed', err);
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  return {
    settings,
    setSettings,
    instructions,
    setInstructions,
    isLoading,
    isSaving,
    saveSuccess,
    setSaveSuccess,
    updateSettings,
    loadSettings
  };
}
