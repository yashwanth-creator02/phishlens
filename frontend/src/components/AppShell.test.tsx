import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { SessionProvider } from "../auth";
import { AppShell } from "./AppShell";

function renderShell(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <SessionProvider>
        <AppShell />
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe("AppShell", () => {
  it("marks the active route", () => {
    renderShell("/history");
    expect(screen.getByRole("link", { name: /^history$/i })).toHaveAttribute("aria-current", "page");
  });

  it("separates the working screens from the reference screens", () => {
    renderShell("/");
    const nav = screen.getByRole("navigation", { name: "Primary" });
    expect(nav).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^dashboard$/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^history$/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^model$/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^how it works$/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^status$/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^profile$/i })).toBeInTheDocument();
  });

  it("renders sidebar toggle button that collapses and expands sidebar", () => {
    renderShell("/");
    const toggleBtn = screen.getByRole("button", { name: /collapse sidebar/i });
    expect(toggleBtn).toBeInTheDocument();
    fireEvent.click(toggleBtn);
    expect(screen.getByRole("button", { name: /expand sidebar/i })).toBeInTheDocument();
  });

  it("renders theme toggle button and toggles theme", () => {
    renderShell("/");
    const toggle = screen.getByRole("button", { name: /theme/i });
    expect(toggle).toBeInTheDocument();
    expect(toggle).toHaveAttribute("aria-pressed");
    fireEvent.click(toggle);
    expect(toggle).toBeInTheDocument();
  });
});
