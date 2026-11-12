import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Profile from "./Profile";
import { SessionProvider } from "../auth";
import { api, ApiError } from "../api/client";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      alias: vi.fn(),
      baseline: vi.fn(),
    },
  };
});

describe("Profile verification gate and data handling", () => {
  it("shows forwarding address when verified", async () => {
    vi.mocked(api.alias).mockResolvedValueOnce({ address: "u-123@phishlens.test", token: "123" });
    render(
      <MemoryRouter>
        <SessionProvider>
          <Profile />
        </SessionProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByText("u-123@phishlens.test")).toBeInTheDocument();
  });

  it("shows verify panel when unverified (403)", async () => {
    vi.mocked(api.alias).mockRejectedValueOnce(new ApiError(403, "Verify your email address before using a forwarding alias"));
    render(
      <MemoryRouter>
        <SessionProvider>
          <Profile />
        </SessionProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByRole("region", { name: /verify your email address/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /resend verification email/i })).toBeInTheDocument();
  });

  it("renders data handling section", async () => {
    vi.mocked(api.alias).mockResolvedValueOnce({ address: "u-123@phishlens.test", token: "123" });
    render(
      <MemoryRouter>
        <SessionProvider>
          <Profile />
        </SessionProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByRole("region", { name: /data handling/i })).toBeInTheDocument();
  });
});
