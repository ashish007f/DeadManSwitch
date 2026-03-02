import { Check } from 'lucide-react';
import { useSettings } from '../../../hooks/useSettings';
import { Spinner } from '../../../components/ui';

interface SettingsPanelProps {
  onClose: () => void;
  onSaveSuccess: () => void;
}

export function SettingsPanel({ onClose, onSaveSuccess }: SettingsPanelProps) {
  const {
    settings,
    setSettings,
    instructions,
    setInstructions,
    isLoading,
    isSaving,
    saveSuccess,
    updateSettings
  } = useSettings();

  async function handleSave() {
    const success = await updateSettings();
    if (success) {
      setTimeout(onSaveSuccess, 800);
    }
  }

  if (isLoading) return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <Spinner size={32} />
    </div>
  );

  return (
    <div className="form-card">
      <div className="form-group">
        <label>Check-In Interval (hours)</label>
        <input 
          type="number" 
          step="any"
          value={settings?.checkin_interval_hours ?? ''} 
          onChange={e => {
            const val = e.target.value === '' ? null : parseFloat(e.target.value);
            setSettings(s => s ? {...s, checkin_interval_hours: val} : null);
          }}
        />
        <p className="form-hint">How often should you check in?</p>
      </div>

      <div className="form-group">
        <label>Missed Buffer (hours)</label>
        <input 
          type="number" 
          step="any"
          value={settings?.missed_buffer_hours ?? ''} 
          onChange={e => {
            const val = e.target.value === '' ? null : parseFloat(e.target.value);
            setSettings(s => s ? {...s, missed_buffer_hours: val} : null);
          }}
        />
        <p className="form-hint">Extra time before the interval is considered MISSED.</p>
      </div>

      <div className="form-group">
        <label>Grace Period (hours)</label>
        <input 
          type="number" 
          step="any"
          value={settings?.grace_period_hours ?? ''} 
          onChange={e => {
            const val = e.target.value === '' ? null : parseFloat(e.target.value);
            setSettings(s => s ? {...s, grace_period_hours: val} : null);
          }}
        />
        <p className="form-hint">Extra time after MISSED before contacts get full instructions.</p>
      </div>

      <div className="form-group">
        <label>Trusted Contacts</label>
        <input 
          type="text" 
          placeholder="comma separated emails"
          value={settings?.contacts?.join(', ') || ''} 
          onChange={e => setSettings(s => s ? {...s, contacts: e.target.value.split(',').map(c => c.trim()).filter(Boolean)} : null)}
        />
      </div>

      <div className="form-group">
        <label>Emergency Instructions</label>
        <textarea 
          rows={6}
          placeholder="Example: Bank name/branch/account no, PF account, MF account, Locker location etc."
          value={instructions}
          onChange={e => setInstructions(e.target.value)}
        />
        <p className="form-hint" style={{ color: 'var(--text-muted)' }}>
          <strong>Important:</strong> DO NOT store passwords here.
        </p>
        <p className="form-hint">
          These details will be emailed to your contacts ONLY if you miss your check-in after the grace period expires.
        </p>
      </div>

      <div className="form-actions">
        <button className="btn-secondary" onClick={onClose}>Close</button>
        <button className="btn-primary" onClick={handleSave} disabled={isSaving}>
          {isSaving ? <Spinner /> : (saveSuccess ? <Check size={20} /> : 'Save Changes')}
        </button>
      </div>
    </div>
  );
}
