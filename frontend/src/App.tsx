import { useEffect, useState } from "react";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";
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

  if (!ready) {
    return <p className="muted pad">Initializing authentication session...</p>;
  }

  const needsLogin = !!supabase && !session;

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <header className="topbar">
        <NavLink to="/" className="brand">PhishLens</NavLink>
        <nav aria-label="Main navigation">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>Analyses</NavLink>
          <NavLink to="/settings" className={({ isActive }) => (isActive ? "active" : "")}>Settings</NavLink>
          {supabase && session && (
            <button className="link" onClick={() => void supabase!.auth.signOut()} type="button">
              Sign out
            </button>
          )}
        </nav>
      </header>

      {health && !health.model_loaded && (
        <div className="banner warn">
          Warning: No trained model is loaded. {health.detail ?? "Run backend training command."}
        </div>
      )}

      <main id="main-content">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={needsLogin ? <Navigate to="/login" /> : <Dashboard />} />
          <Route path="/analyses/:id" element={needsLogin ? <Navigate to="/login" /> : <AnalysisDetailPage />} />
          <Route path="/settings" element={needsLogin ? <Navigate to="/login" /> : <Settings />} />
        </Routes>
      </main>

      <footer className="footer">
        PhishLens version 0.1 triage console. Explanations derive from SHAP contributions checked against email evidence.
        <br />
        This software is not a substitute for professional security judgment.
      </footer>
    </div>
  );
}
