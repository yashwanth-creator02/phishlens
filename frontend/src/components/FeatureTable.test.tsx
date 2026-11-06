import { afterEach, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import FeatureTable, { sortContributions } from "./FeatureTable";

afterEach(() => {
  document.body.innerHTML = "";
});

describe("sortContributions", () => {
  it("sorts by absolute contribution descending without mutating the input", () => {
    const rows = [
      { name: "b", contribution: -0.2 },
      { name: "a", contribution: 0.9 },
      { name: "c", contribution: 0.5 },
    ];
    expect(sortContributions(rows).map((r) => r.name)).toEqual(["a", "c", "b"]);
    expect(rows.map((r) => r.name)).toEqual(["b", "a", "c"]);
  });
});

describe("FeatureTable", () => {
  it("shows the largest contribution first", () => {
    render(
      <FeatureTable
        rows={[
          { name: "b", group: "header", value: 0, contribution: -0.2 },
          { name: "a", group: "header", value: 1, contribution: 0.9 },
        ]}
      />,
    );
    expect(screen.getAllByRole("row")[1]).toHaveTextContent("a");
  });

  it("has a table caption", () => {
    const { container } = render(
      <FeatureTable
        rows={[{ name: "a", group: "url", value: 1, contribution: 0.9 }]}
      />,
    );
    const table = container.querySelector("table");
    expect(table).not.toBeNull();
    expect(table?.textContent).toMatch(/SHAP/);
    expect(screen.getByText(/Top feature contributions/)).toBeDefined();
  });

  it("shows only the top 20 by absolute contribution", () => {
    const rows = Array.from({ length: 30 }, (_, i) => ({
      name: `f${i}`,
      group: "text",
      value: i,
      contribution: (i + 1) / 100,
    }));
    render(<FeatureTable rows={rows} />);
    const bodyRows = screen.getAllByRole("row").slice(1);
    expect(bodyRows).toHaveLength(20);
    expect(bodyRows[0]).toHaveTextContent("f29");
  });
});
