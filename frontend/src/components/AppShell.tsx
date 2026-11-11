import { NavLink, Outlet } from "react-router-dom";
import { useSession } from "../auth";
import { ToastProvider } from "./Toast";
import { ConfirmProvider } from "./ConfirmDialog";
import "../styles/shell.css";

// Primary: the two screens an analyst works in, all day.
const primary = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/history", label: "History" },
];

// Reference: what the system is and how it behaves.
const reference = [
  { to: "/model", label: "Model" },
  { to: "/how-it-works", label: "How it works" },
  { to: "/status", label: "Status" },
];

function Shell() {
  const { user } = useSession();

  return (
    <div className="shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="shell-header">
        <NavLink to="/" className="shell-brand" end>
          PhishLens<span>Explainable email triage</span>
        </NavLink>

        <nav className="shell-nav" aria-label="Primary">
          {primary.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? "shell-link is-active" : "shell-link")}
            >
              {link.label}
            </NavLink>
          ))}
          <span className="shell-separator" aria-hidden="true" />
          {reference.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => (isActive ? "shell-link is-active" : "shell-link")}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="shell-account">
          {user?.email && <span className="shell-account-email mono" title={user.email}>{user.email}</span>}
          <NavLink to="/profile" className={({ isActive }) => (isActive ? "shell-link is-active" : "shell-link")}>
            Profile
          </NavLink>
        </div>
      </header>
      <main id="main-content" className="shell-main" tabIndex={-1}><Outlet /></main>
      <footer className="shell-footer">
        <span>PhishLens v0.1</span>
        <span>Evidence-verified reasons. Not a replacement for judgement.</span>
      </footer>
    </div>
  );
}

export function AppShell() {
  return (
    <ToastProvider>
      <ConfirmProvider>
        <Shell />
      </ConfirmProvider>
    </ToastProvider>
  );
}
