import { Mail } from 'lucide-react';

export function SupportPanel() {
  return (
    <div className="fade-in">
      <div className="card">
        <h2 style={{ marginBottom: '12px' }}>Support & Feedback</h2>
        <p style={{ marginBottom: '24px' }}>
          Have questions or suggestions? We're here to help.
        </p>

        <div className="list-vertical" style={{ margin: 0 }}>
          <div className="list-item" style={{ background: '#f8fafc', padding: '16px', borderRadius: '16px', border: '1px solid var(--border)', opacity: 0.7 }}>
            <div className="list-item-icon" style={{ background: 'white', boxShadow: 'var(--shadow-sm)' }}>
              <Mail size={18} color="var(--text-muted)" />
            </div>
            <div className="list-content" style={{ flex: 1 }}>
              <h3 style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Email Support</h3>
              <p style={{ fontSize: '12px' }}>Coming Soon</p>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '32px', textAlign: 'center' }}>
          <p style={{ fontSize: '11px' }}>
            I'mGood v0.1.0 • Made with ❤️ for safety.
          </p>
        </div>
      </div>
    </div>
  );
}
