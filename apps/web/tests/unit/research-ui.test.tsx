import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FactorBars, ScoreBadge, Sparkline } from "../../components/ResearchUI";

describe("research UI", () => {
  it("renders score and factor values with text alternatives", () => {
    render(
      <>
        <ScoreBadge band="Candidate" score={72.4} />
        <FactorBars values={{ momentum: 88.2, quality: null }} />
      </>,
    );
    expect(screen.getByText("72.4 · Candidate")).toBeInTheDocument();
    expect(screen.getByText("88.2")).toBeInTheDocument();
    expect(screen.getByText("Missing")).toBeInTheDocument();
  });

  it("adds an accessible summary to a chart", () => {
    render(<Sparkline values={[100, 110, 105]} label="Test equity curve" />);
    expect(
      screen.getByRole("img", { name: "Test equity curve" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/First 100.00; last 105.00/)).toBeInTheDocument();
  });
});
