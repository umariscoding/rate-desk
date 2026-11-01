import { useQueryClient } from "@tanstack/react-query";
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { logIn } from "../api/auth";
import type { User } from "../api/types";
import { clearSession, loadSession, saveSession, SESSION_EXPIRED_EVENT } from "../lib/session";

interface SessionContextValue {
  user: User | null;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(() => loadSession()?.user ?? null);

  const signOut = useCallback(() => {
    clearSession();
    queryClient.clear(); // Nothing the last person saw may linger for the next one.
    setUser(null);
  }, [queryClient]);

  const signIn = useCallback(async (username: string, password: string) => {
    const session = await logIn(username, password);
    saveSession(session);
    setUser(session.user);
  }, []);

  useEffect(() => {
    window.addEventListener(SESSION_EXPIRED_EVENT, signOut);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, signOut);
  }, [signOut]);

  const value = useMemo(() => ({ user, signIn, signOut }), [user, signIn, signOut]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const value = useContext(SessionContext);
  if (value === null) throw new Error("useSession must be used inside SessionProvider");
  return value;
}
