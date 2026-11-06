import { Link } from "react-router-dom";

export function SessionExpired({ open }: { open: boolean }) {
  if (!open) return null;
  return (
    <div className="dialog-backdrop">
      <div className="dialog" role="alertdialog" aria-modal="true" aria-labelledby="session-title">
        <h2 id="session-title">Session expired</h2>
        <p>Your session ended. Sign in again to keep working; nothing was deleted.</p>
        <div className="dialog-actions">
          <Link className="btn btn-accent" to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
