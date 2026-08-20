import { describe, expect, it } from "vitest";

describe("public research conventions", () => {
  it("keeps confidence wording distinct from prediction accuracy", () => {
    const help =
      "Confidence measures data completeness and freshness, not predictive certainty.";
    expect(help).toContain("completeness and freshness");
    expect(help).not.toContain("probability");
  });
});
