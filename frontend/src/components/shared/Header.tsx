import { LogOut } from 'lucide-react';
import type { User } from '../../types';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

export function Header({ user, onLogout }: HeaderProps) {
  if (!user) return null;

  return (
    <header className="app-header">
      <div className="brand">
        <div className="hero-icon indigo" style={{ width: '36px', height: '36px', margin: 0, borderRadius: '10px' }}>
          <img src="/icon.svg" alt="logo" style={{ width: '24px', height: '24px' }} />
        </div>
        <h1>I'mGood</h1>
      </div>
      
      <div className="user-profile">
        <div className="user-pill">
          <span>{user.display_name}</span>
          <button onClick={onLogout} className="logout-btn-minimal" title="Logout">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}
