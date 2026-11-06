import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { RequireAuth, useSession } from "./auth";
import { api } from "./api/client";
import type { Health } from "./types";
import { AppShell } from "./components/AppShell";
import Dashboard from "./pages/Dashboard";
import Cases from "./pages/Cases";
import AnalysisDetailPage from "./pages/AnalysisDetail";
import Model from "./pages/Model";
import HowItWorks from "./pages/HowItWorks";
import Settings from "./pages/Settings";
import Status from "./pages/Status";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

export default function App() {
  const { loading } = useSession();
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  if (loading) return <p className="muted pad">Initializing authentication session...</p>;

  return (
    <>
      {health && !health.model_loaded && (
        <div className="banner warn">
          Warning: No trained model is loaded. {health.detail ?? "Run backend training command."}
        </div>
      )}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<RequireAuth><AppShell /></RequireAuth>}>
          <Route index element={<Dashboard />} />
          <Route path="cases" element={<Cases />} />
          <Route path="analyses/:id" element={<AnalysisDetailPage />} />
          <Route path="model" element={<Model />} />
          <Route path="how-it-works" element={<HowItWorks />} />
          <Route path="settings" element={<Settings />} />
          <Route path="status" element={<Status />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
