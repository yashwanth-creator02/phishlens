import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "./supabase";
import { api } from "./api/client";
import type { Health } from "./types";
import Dashboard from "./pages/Dashboard";
import AnalysisDetailPage from "./pages/AnalysisDetail";
import Settings from "./pages/Settings";
import Login from "./pages/Login";

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(!supabase);
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setReady(true);
    });
    const { data } = supabase.auth.onAuthStateChange((_e, s) => setSession(s));
    return () => data.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  if (!ready) return <p className="muted pad">Loading…</p>;
  const needsLogin = !!supabase && !session;

  return (
    <div className="app">
      <header className="topbar">
        <Link to="/" className="brand">PhishLens</Link>
        <nav>
          <Link to="/">Analyses</Link>
          <Link to="/settings">Settings</Link>
          {supabase && session && <button className="link" onClick={() => supabase!.auth.signOut()}>Sign out</button>}
        </nav>
      </header>
      {health && !health.model_loaded && (
        <div className="banner warn">
          No trained model is loaded: {health.detail ?? "run `make train-demo` in the backend."}
        </div>
      )}
      <main>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={needsLogin ? <Navigate to="/login" /> : <Dashboard />} />
          <Route path="/analyses/:id" element={needsLogin ? <Navigate to="/login" /> : <AnalysisDetailPage />} />
          <Route path="/settings" element={needsLogin ? <Navigate to="/login" /> : <Settings />} />
        </Routes>
      </main>
      <footer className="muted pad">
        PhishLens v0.1 · explanations come from SHAP and are checked against the email · not a substitute for your judgement
      </footer>
    </div>
  );
}
