import { render, screen } from "@testing-library/react";
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
    expect(screen.getByRole("link", { name: /^status$/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^profile$/i })).toBeInTheDocument();
  });
});
