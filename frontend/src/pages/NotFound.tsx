import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <section className="page">
      <p className="eyebrow">404</p>
      <h1>Page not found</h1>
      <p className="muted">That address does not match a page in this console.</p>
      <Link className="btn btn-accent" to="/">Back to dashboard</Link>
    </section>
  );
}
