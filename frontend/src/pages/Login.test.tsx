import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Login from "./Login";
import { supabase } from "../supabase";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      forwardingConfig: vi.fn().mockResolvedValue({
        alias_domain: "phishlens.test",
        alias_pattern: "u-<token>@phishlens.test",
        inbound_configured: true,
      }),
    },
  };
});

vi.mock("../supabase", () => ({
  supabase: {
    auth: {
      signInWithOAuth: vi.fn().mockResolvedValue({ data: {}, error: null }),
      signInAnonymously: vi.fn().mockResolvedValue({ data: {}, error: null }),
      signInWithPassword: vi.fn().mockResolvedValue({ data: {}, error: null }),
    },
  },
}));

describe("Login", () => {
  it("renders forwarding panel with domain", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    expect(await screen.findByText("phishlens.test")).toBeInTheDocument();
  });

  it("calls signInWithOAuth on Google button click", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    const googleBtn = await screen.findByRole("button", { name: /continue with google/i });
    const user = userEvent.setup();
    await user.click(googleBtn);
    expect(supabase?.auth.signInWithOAuth).toHaveBeenCalledWith({
      provider: "google",
      options: { redirectTo: window.location.origin },
    });
  });

  it("calls signInAnonymously on guest button click", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    const guestBtn = await screen.findByRole("button", { name: /try it as a guest/i });
    const user = userEvent.setup();
    await user.click(guestBtn);
    expect(supabase?.auth.signInAnonymously).toHaveBeenCalled();
  });
});
