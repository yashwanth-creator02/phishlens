import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import type { Session, User } from "@supabase/supabase-js";
import { supabase } from "./supabase";

type AuthValue = {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<string | null>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(!!supabase);

  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
    return () => data.subscription.unsubscribe();
  }, []);

  const value = useMemo<AuthValue>(() => ({
    session,
    user: session?.user ?? null,
    loading,
    signIn: async (email, password) => {
      if (!supabase) return "Authentication is disabled.";
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      return error?.message ?? null;
    },
    signOut: async () => {
      if (supabase) await supabase.auth.signOut();
    },
  }), [session, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useSession(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useSession must be used inside SessionProvider");
  return value;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { loading, session } = useSession();
  const location = useLocation();
  if (loading) return <p className="muted pad">Initializing authentication session...</p>;
  if (supabase && !session) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <>{children}</>;
}
