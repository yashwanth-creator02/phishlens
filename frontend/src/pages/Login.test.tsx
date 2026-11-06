import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Login from "./Login";

// Helper: renders Login with a mock signIn prop, no supabase, no auth provider.
function renderLogin(signIn: ReturnType<typeof vi.fn>) {
  // Stub the supabase module so it is falsy, forcing the form path.
  vi.doMock("../supabase", () => ({ supabase: null }));
  return render(
    <MemoryRouter>
      <Login signIn={signIn} />
    </MemoryRouter>,
  );
}

describe("Login", () => {
  it("shows a login error next to the field", async () => {
    const mockSignIn = vi.fn().mockRejectedValue(new Error("Invalid login"));
    renderLogin(mockSignIn);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/email address/i), "analyst@example.com");
    await user.type(screen.getByLabelText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText("Invalid login")).toBeInTheDocument();
  });
});
