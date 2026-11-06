import { NavLink, Outlet } from "react-router-dom";
import { ToastProvider } from "./Toast";
import { ConfirmProvider } from "./ConfirmDialog";
import "../styles/shell.css";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/cases", label: "Cases" },
  { to: "/model", label: "Model" },
  { to: "/how-it-works", label: "How it works" },
  { to: "/settings", label: "Settings" },
  { to: "/status", label: "Status" },
];

function Shell() {
  return (
    <div className="shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="shell-header">
        <NavLink to="/" className="shell-brand" end>
          PhishLens<span>Explainable email triage</span>
        </NavLink>
        <nav className="shell-nav" aria-label="Primary">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? "shell-link is-active" : "shell-link")}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
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

