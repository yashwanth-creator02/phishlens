import { useState, useEffect, useRef } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useSession } from "../auth";
import { useForwardingAlias } from "../hooks/useForwardingAlias";
import { ToastProvider } from "./Toast";
import { ConfirmProvider } from "./ConfirmDialog";
import { Logo } from "./Logo";
import "../styles/shell.css";

const workLinks = [
  {
    to: "/",
    label: "Dashboard",
    end: true,
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="3" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="14" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
  },
  {
    to: "/history",
    label: "History",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="9"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
    ),
  },
];

const referenceLinks = [
  {
    to: "/model",
    label: "Model",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <polygon points="12 2 2 7 12 12 22 7 12 2"/>
        <polyline points="2 17 12 22 22 17"/>
        <polyline points="2 12 12 17 22 12"/>
      </svg>
    ),
  },
  {
    to: "/how-it-works",
    label: "How it works",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
      </svg>
    ),
  },
  {
    to: "/status",
    label: "Status",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
      </svg>
    ),
  },
];

const profileLink = {
  to: "/profile",
  label: "Profile",
  icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  ),
};

function Shell() {
  const { user } = useSession();
  const aliasState = useForwardingAlias();
  const [copiedSidebar, setCopiedSidebar] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem("phishlens-sidebar-collapsed") === "true";
  });
  const location = useLocation();
  const menuBtnRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  const toggleCollapse = () => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("phishlens-sidebar-collapsed", String(next));
      return next;
    });
  };

  const [theme, setTheme] = useState<"light" | "dark">(() => {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  });

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
      localStorage.setItem("phishlens-theme", "dark");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("phishlens-theme", "light");
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === "dark" ? "light" : "dark"));
  };

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
      drawerRef.current?.focus();
    } else {
      document.body.style.overflow = "";
      menuBtnRef.current?.focus();
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && mobileOpen) {
        setMobileOpen(false);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileOpen]);

  const renderNavLinks = () => (
    <>
      <div className="nav-group">
        <span className="nav-group-label" id="nav-work-label">Work</span>
        <div className="nav-group-items" role="group" aria-labelledby="nav-work-label">
          {workLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? "shell-link is-active" : "shell-link")}
            >
              {link.icon}
              <span>{link.label}</span>
            </NavLink>
          ))}
        </div>
      </div>

      <div className="nav-group">
        <span className="nav-group-label" id="nav-ref-label">Reference</span>
        <div className="nav-group-items" role="group" aria-labelledby="nav-ref-label">
          {referenceLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => (isActive ? "shell-link is-active" : "shell-link")}
            >
              {link.icon}
              <span>{link.label}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </>
  );

  return (
    <div className="shell">
      <a className="skip-link" href="#main-content">Skip to content</a>

      <header className="mobile-topbar" aria-label="Mobile Navigation Bar">
        <NavLink to="/" className="shell-brand" end>
          <span className="brand-title">
            <Logo size={20} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
            PhishLens
          </span>
          <span className="brand-subtitle">Explainable email triage</span>
        </NavLink>
        <button
          ref={menuBtnRef}
          className="mobile-menu-btn"
          aria-expanded={mobileOpen}
          aria-controls="sidebar-drawer"
          aria-label="Toggle navigation menu"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          )}
        </button>
      </header>

      {mobileOpen && (
        <div className="sidebar-backdrop" onClick={() => setMobileOpen(false)} aria-hidden="true" />
      )}

      <div className="shell-body">
        <aside
          id="sidebar-drawer"
          ref={drawerRef}
          tabIndex={-1}
          role="navigation"
          aria-label="Primary"
          className={`shell-sidebar ${mobileOpen ? "is-open" : ""} ${collapsed ? "is-collapsed" : ""}`}
        >
          <div className="sidebar-header">
            <div className="sidebar-header-brand">
              <button
                type="button"
                className="sidebar-toggle-btn"
                onClick={() => {
                  if (mobileOpen) {
                    setMobileOpen(false);
                  } else {
                    toggleCollapse();
                  }
                }}
                aria-label={
                  mobileOpen
                    ? "Close navigation sidebar"
                    : collapsed
                    ? "Expand sidebar"
                    : "Collapse sidebar"
                }
                title={
                  mobileOpen
                    ? "Close navigation sidebar"
                    : collapsed
                    ? "Expand sidebar"
                    : "Collapse sidebar"
                }
              >
                <span className="sidebar-toggle-icon-default">
                  <Logo size={22} />
                </span>
                <span className="sidebar-toggle-icon-hover" aria-hidden="true">
                  {mobileOpen ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18"/>
                      <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  ) : collapsed ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="15 18 9 12 15 6" />
                    </svg>
                  )}
                </span>
              </button>

              {!collapsed && (
                <NavLink to="/" className="shell-brand" end onClick={() => setMobileOpen(false)}>
                  <span className="brand-title">PhishLens</span>
                  <span className="brand-subtitle">Explainable email triage</span>
                </NavLink>
              )}
            </div>
          </div>

          <div className="shell-nav">
            {renderNavLinks()}
          </div>

          <div className="shell-forwarding-widget">
            {!collapsed ? (
              <>
                <div className="shell-forwarding-header">
                  <span className="shell-forwarding-label">Forward Email</span>
                  {aliasState.status === "verified" && (
                    <span className="shell-forwarding-badge">Active</span>
                  )}
                </div>
                {aliasState.status === "verified" ? (
                  <div className="shell-forwarding-body">
                    <span className="shell-forwarding-address mono" title={aliasState.address}>
                      {aliasState.address}
                    </span>
                    <div className="shell-forwarding-actions">
                      <button
                        type="button"
                        className="shell-forwarding-btn"
                        onClick={() => {
                          navigator.clipboard.writeText(aliasState.address);
                          setCopiedSidebar(true);
                          setTimeout(() => setCopiedSidebar(false), 2000);
                        }}
                        title="Copy forwarding email address"
                        aria-label="Copy forwarding address"
                      >
                        {copiedSidebar ? (
                          <>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                            </svg>
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                      <a
                        href={`mailto:${aliasState.address}`}
                        onClick={() => {
                          navigator.clipboard.writeText(aliasState.address);
                          setCopiedSidebar(true);
                          setTimeout(() => setCopiedSidebar(false), 2000);
                        }}
                        className="shell-forwarding-btn mail-link"
                        title="Copy address and open mail app"
                        aria-label="Copy address and open mail app"
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <line x1="22" y1="2" x2="11" y2="13"/>
                          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                        </svg>
                        <span>Mail App</span>
                      </a>
                    </div>
                  </div>
                ) : (
                  <div className="shell-forwarding-body">
                    <NavLink
                      to="/profile"
                      className="shell-forwarding-subtle-link"
                      onClick={() => setMobileOpen(false)}
                    >
                      {aliasState.status === "unverified"
                        ? "Verify email for alias →"
                        : "Sign in for forwarding alias →"}
                    </NavLink>
                  </div>
                )}
              </>
            ) : (
              <div className="shell-forwarding-collapsed">
                {aliasState.status === "verified" ? (
                  <button
                    type="button"
                    className="shell-forwarding-icon-btn"
                    onClick={() => {
                      navigator.clipboard.writeText(aliasState.address);
                      setCopiedSidebar(true);
                      setTimeout(() => setCopiedSidebar(false), 2000);
                    }}
                    title={copiedSidebar ? "Copied!" : `Copy ${aliasState.address}`}
                    aria-label={`Copy forwarding address ${aliasState.address}`}
                  >
                    {copiedSidebar ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--low)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                        <polyline points="22,6 12,13 2,6"/>
                      </svg>
                    )}
                  </button>
                ) : (
                  <NavLink
                    to="/profile"
                    className="shell-forwarding-icon-btn"
                    title="Forwarding alias setup"
                    aria-label="Forwarding alias setup"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                      <polyline points="22,6 12,13 2,6"/>
                    </svg>
                  </NavLink>
                )}
              </div>
            )}
          </div>

          <div className="shell-account">
            {user?.email && (
              <span className="shell-account-email mono" title={user.email}>
                {user.email}
              </span>
            )}
            <div className="shell-account-row">
              <NavLink
                to={profileLink.to}
                className={({ isActive }) => (isActive ? "shell-link is-active" : "shell-link")}
                onClick={() => setMobileOpen(false)}
              >
                {profileLink.icon}
                <span>{profileLink.label}</span>
              </NavLink>
              <button
                type="button"
                className="theme-toggle-btn"
                aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
                aria-pressed={theme === "dark"}
                onClick={toggleTheme}
              >
                {theme === "dark" ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <circle cx="12" cy="12" r="5"/>
                    <line x1="12" y1="1" x2="12" y2="3"/>
                    <line x1="12" y1="21" x2="12" y2="23"/>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                    <line x1="1" y1="12" x2="3" y2="12"/>
                    <line x1="21" y1="12" x2="23" y2="12"/>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                  </svg>
                )}
              </button>
            </div>
          </div>
        </aside>

        <div className="shell-content-area">
          <main id="main-content" className="shell-main" tabIndex={-1}>
            <Outlet />
          </main>
          <footer className="shell-footer">
            <span>PhishLens v0.1</span>
            <span>Evidence-verified reasons. Not a replacement for judgement.</span>
          </footer>
        </div>
      </div>
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
