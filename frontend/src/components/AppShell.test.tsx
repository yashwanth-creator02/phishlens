import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AppShell } from "./AppShell";

describe("AppShell", () => {
  it("marks the active route", () => {
    render(
      <MemoryRouter initialEntries={["/cases"]}>
        <AppShell />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: /^cases$/i })).toHaveAttribute("aria-current", "page");
  });
});
