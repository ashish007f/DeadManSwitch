import { LogOut, CheckCircle } from 'lucide-react';
import type { User } from '../../types';

interface HeaderProps {
  user: User;
  onLogout: () => void;
}

export function Header({ user, onLogout }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="brand">
        <CheckCircle size={22} color="var(--primary)" style={{ flexShrink: 0 }} />
        <h1>I'mGood</h1>
      </div>
      <div className="user-profile">
        <div className="display-name">{user.display_name || user.phone}</div>
        <button className="logout-btn" onClick={onLogout}>
          <LogOut size={12} style={{ marginRight: 4 }} /> Logout
        </button>
      </div>
    </header>
  );
}
