import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Vitest does not enable Testing Library's automatic cleanup unless globals are on,
// so mounted trees would otherwise leak between test files.
afterEach(() => cleanup());
