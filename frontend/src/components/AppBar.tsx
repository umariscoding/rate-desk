import type { User } from "../api/types";
import { ROLE_LABEL } from "../lib/session";

export interface Tab {
  id: string;
  label: string;
}

interface Props {
  user: User;
  tabs: Tab[];
  current: string;
  onChange: (tabId: string) => void;
  onSignOut: () => void;
}

export function AppBar({ user, tabs, current, onChange, onSignOut }: Props) {
  return (
    <header className="appbar">
      <span className="appbar__logo">Rate Desk</span>
      <nav className="appbar__tabs" aria-label="Main">
        {tabs.map((tab) => (
          <button key={tab.id} className="appbar__tab" aria-current={tab.id === current ? "page" : undefined} onClick={() => onChange(tab.id)}>
            {tab.label}
          </button>
        ))}
      </nav>
      <div className="appbar__user">
        <span>
          <strong>{user.display_name}</strong>
          <span className="appbar__role">{ROLE_LABEL[user.role]}</span>
        </span>
        <button className="appbar__signout" onClick={onSignOut}>
          Sign out
        </button>
      </div>
    </header>
  );
}
