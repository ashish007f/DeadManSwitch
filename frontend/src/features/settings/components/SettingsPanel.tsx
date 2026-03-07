import { Check, Plus, Trash2, ShieldCheck, Mail, Clock, AlertTriangle } from 'lucide-react';
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

  const addContact = () => {
    setSettings(s => s ? { ...s, contacts: [...(s.contacts || []), ''] } : null);
  };

  const removeContact = (index: number) => {
    setSettings(s => s ? { 
      ...s, 
      contacts: (s.contacts || []).filter((_, i) => i !== index) 
    } : null);
  };

  const updateContact = (index: number, value: string) => {
    setSettings(s => s ? {
      ...s,
      contacts: (s.contacts || []).map((c, i) => i === index ? value : c)
    } : null);
  };

  if (isLoading) return (
    <div style={{ padding: 60, textAlign: 'center' }}>
      <Spinner size={32} />
      <p style={{ marginTop: 12 }}>Loading your secure settings...</p>
    </div>
  );

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <section className="card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <div className="hero-icon indigo" style={{ width: 40, height: 40, marginBottom: 0 }}>
            <Clock size={20} />
          </div>
          <h2 style={{ margin: 0 }}>Intervals</h2>
        </div>

        <div className="form-group">
          <label>Check-In Frequency (hours)</label>
          <input 
            type="number" 
            step="any"
            value={settings?.checkin_interval_hours ?? ''} 
            onChange={e => {
              const val = e.target.value === '' ? null : parseFloat(e.target.value);
              setSettings(s => s ? {...s, checkin_interval_hours: val} : null);
            }}
            placeholder="e.g. 48"
          />
          <p className="form-hint">How often do you want to check in?</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="form-group">
            <label>Missed Buffer</label>
            <input 
              type="number" 
              step="any"
              value={settings?.missed_buffer_hours ?? ''} 
              onChange={e => {
                const val = e.target.value === '' ? null : parseFloat(e.target.value);
                setSettings(s => s ? {...s, missed_buffer_hours: val} : null);
              }}
            />
            <p className="form-hint">Buffer before status becomes MISSED.</p>
          </div>

          <div className="form-group">
            <label>Grace Period</label>
            <input 
              type="number" 
              step="any"
              value={settings?.grace_period_hours ?? ''} 
              onChange={e => {
                const val = e.target.value === '' ? null : parseFloat(e.target.value);
                setSettings(s => s ? {...s, grace_period_hours: val} : null);
              }}
            />
            <p className="form-hint">Wait time after MISSED before alerting.</p>
          </div>
        </div>
      </section>

      <section className="card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <div className="hero-icon green" style={{ width: 40, height: 40, marginBottom: 0 }}>
            <Mail size={20} />
          </div>
          <h2 style={{ margin: 0 }}>Trusted Contacts</h2>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
          {(settings?.contacts || []).map((contact, index) => (
            <div key={index} style={{ display: 'flex', gap: 8 }}>
              <input 
                type="email" 
                placeholder="email@example.com"
                value={contact} 
                onChange={e => updateContact(index, e.target.value)}
                style={{ flex: 1 }}
              />
              <button 
                onClick={() => removeContact(index)}
                style={{ 
                  padding: '0 12px', 
                  color: 'var(--error)', 
                  background: '#fef2f2',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <Trash2 size={18} />
              </button>
            </div>
          ))}
          
          {(settings?.contacts || []).length === 0 && (
            <p style={{ textAlign: 'center', padding: '12px', border: '1px dashed var(--border)', borderRadius: '12px' }}>
              No contacts added yet.
            </p>
          )}

          <button className="btn-secondary" onClick={addContact} style={{ marginTop: 4 }}>
            <Plus size={18} /> Add Another Contact
          </button>
        </div>
      </section>

      <section className="card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <div className="hero-icon blue" style={{ width: 40, height: 40, marginBottom: 0 }}>
            <AlertTriangle size={20} />
          </div>
          <h2 style={{ margin: 0 }}>Emergency Instructions</h2>
        </div>

        <div className="form-group">
          <textarea 
            rows={8}
            placeholder="Example: Bank name/branch/account no, Locker location, insurance details, etc."
            value={instructions}
            onChange={e => setInstructions(e.target.value)}
            style={{ fontSize: '15px', lineHeight: '1.6' }}
          />
          <div style={{ 
            marginTop: 12, 
            padding: '12px', 
            background: '#f8fafc', 
            borderRadius: '12px',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 10
          }}>
            <ShieldCheck size={20} style={{ color: 'var(--success)', flexShrink: 0, marginTop: 2 }} />
            <div>
              <p style={{ fontWeight: 600, color: 'var(--text)', fontSize: '13px', marginBottom: 2 }}>
                End-to-End Encrypted
              </p>
              <p style={{ fontSize: '12px', margin: 0 }}>
                Instructions are encrypted before they leave your device and can only be read by your trusted contacts if you miss your check-in.
              </p>
            </div>
          </div>
        </div>
      </section>

      <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
        <button className="btn-secondary" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
        <button className="btn-primary btn-gradient" onClick={handleSave} disabled={isSaving} style={{ flex: 2 }}>
          {isSaving ? <Spinner /> : (saveSuccess ? <Check size={20} /> : 'Save Securely')}
        </button>
      </div>
    </div>
  );
}
