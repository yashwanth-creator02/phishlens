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

  it("shows a pending label and locks the other buttons while sign-in runs", async () => {
    // A promise that never settles, so the request is still in flight when we assert.
    vi.mocked(supabase!.auth.signInWithPassword).mockReturnValue(new Promise(() => {}) as never);
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    const signInBtn = await screen.findByRole("button", { name: /sign in/i });
    const googleBtn = await screen.findByRole("button", { name: /continue with google/i });
    const guestBtn = await screen.findByRole("button", { name: /try it as a guest/i });

    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/email address/i), "analyst@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "correct-horse-battery");
    await user.click(signInBtn);

    expect(await screen.findByRole("button", { name: /signing in/i })).toBeDisabled();
    expect(googleBtn).toBeDisabled();
    expect(guestBtn).toBeDisabled();
  });

  it("turns a network failure into a message a person can act on", async () => {
    vi.mocked(supabase!.auth.signInWithPassword).mockRejectedValue(new TypeError("Failed to fetch"));
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    const signInBtn = await screen.findByRole("button", { name: /sign in/i });
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/email address/i), "analyst@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "correct-horse-battery");
    await user.click(signInBtn);

    expect(await screen.findByRole("alert")).toHaveTextContent(/could not reach the server/i);
    expect(screen.queryByText(/failed to fetch/i)).not.toBeInTheDocument();
  });
});
