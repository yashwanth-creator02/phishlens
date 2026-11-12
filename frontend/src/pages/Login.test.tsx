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
      signUp: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
    },
  },
}));

describe("Login", () => {
  it("renders two-column layout with brand block and forwarding panel", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    expect(await screen.findByText("phishlens.test")).toBeInTheDocument();
    expect(screen.getByText("Explainable phishing-triage console")).toBeInTheDocument();
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

  it("lets the analyst see the password they are typing", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    const password = await screen.findByLabelText(/^password$/i);
    expect(password).toHaveAttribute("type", "password");

    const toggle = screen.getByRole("button", { name: /show password/i });
    const user = userEvent.setup();
    await user.click(toggle);

    expect(password).toHaveAttribute("type", "text");
    expect(screen.getByRole("button", { name: /hide password/i })).toBeInTheDocument();
  });

  it("marks the fields so a password manager can fill them", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    expect(await screen.findByLabelText(/email address/i)).toHaveAttribute("autocomplete", "email");
    expect(screen.getByLabelText(/^password$/i)).toHaveAttribute("autocomplete", "current-password");
  });

  it("switches to create account mode and shows confirmation message on sign up", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /create an account/i }));
    expect(screen.getByRole("heading", { name: /create an account/i })).toBeInTheDocument();

    await user.type(screen.getByLabelText(/email address/i), "new@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "secret123");
    await user.click(screen.getByRole("button", { name: /^create account$/i }));

    expect(supabase?.auth.signUp).toHaveBeenCalledWith({
      email: "new@example.com",
      password: "secret123",
    });
    expect(await screen.findByText(/check your email to confirm the address/i)).toBeInTheDocument();
  });

  it("dismisses forwarding notification when dismiss button is clicked", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    expect(await screen.findByText("phishlens.test")).toBeInTheDocument();
    const dismissBtn = screen.getByRole("button", { name: /dismiss/i });
    const user = userEvent.setup();
    await user.click(dismissBtn);
    expect(screen.queryByText("phishlens.test")).not.toBeInTheDocument();
  });
});
