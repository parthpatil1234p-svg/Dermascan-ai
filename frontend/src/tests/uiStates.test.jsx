import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DemoModeNotice from "../components/DemoModeNotice";
import ErrorMessage from "../components/ErrorMessage";

describe("shared UI states", () => {
  it("announces validation errors accessibly", () => {
    render(<ErrorMessage id="email-error" message="Please enter a valid email." />);
    expect(screen.getByText("Please enter a valid email.")).toHaveAttribute(
      "role",
      "alert",
    );
  });

  it("labels demonstration output without rendering when inactive", () => {
    const { rerender } = render(<DemoModeNotice visible={false} />);
    expect(screen.queryByText("Demonstration Mode")).not.toBeInTheDocument();
    rerender(<DemoModeNotice visible />);
    expect(screen.getByText("Demonstration Mode")).toBeVisible();
    expect(screen.getByText(/not inference from an evaluated trained model/i)).toBeVisible();
  });
});

