import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { useSession, RequireAuth } from "./auth";
import { api } from "./api/client";
import type { Health } from "./types";
import Dashboard from "./pages/Dashboard";
import AnalysisDetailPage from "./pages/AnalysisDetail";
import Settings from "./pages/Settings";
import Login from "./pages/Login";

export default function App() {
  const { session, loading, signOut } = useSession();
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  if (loading) {
    return <p className="muted pad">Initializing authentication session...</p>;
  }

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <header className="topbar">
        <NavLink to="/" className="brand">PhishLens</NavLink>
        <nav aria-label="Main navigation">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>Analyses</NavLink>
          <NavLink to="/settings" className={({ isActive }) => (isActive ? "active" : "")}>Settings</NavLink>
          {session && (
            <button className="link" onClick={() => void signOut()} type="button">
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
          <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="/analyses/:id" element={<RequireAuth><AnalysisDetailPage /></RequireAuth>} />
          <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
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
