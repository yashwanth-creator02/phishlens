import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiFetch", () => {
  it("adds the bearer token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/api/analyses", { token: "abc" });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer abc");
  });

  it("throws ApiError with status and detail", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "nope" }), { status: 400 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const error = await apiFetch("/api/analyses").catch((err) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 400, message: "nope" });
  });
});
