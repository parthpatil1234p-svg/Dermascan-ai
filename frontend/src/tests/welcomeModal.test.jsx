import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import WelcomeModal from "../components/WelcomeModal";

describe("WelcomeModal component", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("renders welcome title, instructions, and developer information on first session open", () => {
    render(<WelcomeModal />);

    expect(screen.getByText(/Welcome to DermaScan AI!/i)).toBeInTheDocument();
    expect(
      screen.getByText(/uses AI-based facial image analysis to provide general skincare guidance/i)
    ).toBeInTheDocument();

    // Instructions verification
    expect(
      screen.getByText(/Upload a clear, front-facing facial image/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Make sure the face is properly visible and well-lit/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Avoid sunglasses, masks, heavy filters, or extreme angles/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Use a recent image for better analysis/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Enter the required user information accurately/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/The AI analysis provides general skincare guidance only/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Results are not a medical diagnosis/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Product recommendations are based on the detected skin type/i
      )
    ).toBeInTheDocument();

    // Developer / Team details verification
    expect(screen.getByText(/Parth Patil/i)).toBeInTheDocument();
    expect(screen.getByText(/25110042/i)).toBeInTheDocument();
    expect(screen.getByText(/Suyog Pawar/i)).toBeInTheDocument();
    expect(screen.getByText(/25110045/i)).toBeInTheDocument();
    expect(screen.getAllByText(/DermaScan AI/i).length).toBeGreaterThan(0);
  });

  it("closes and sets sessionStorage flag when clicking 'Get Started'", () => {
    render(<WelcomeModal />);

    const getStartedBtn = screen.getByRole("button", { name: /Get Started/i });
    fireEvent.click(getStartedBtn);

    expect(screen.queryByText(/Welcome to DermaScan AI!/i)).not.toBeInTheDocument();
    expect(sessionStorage.getItem("dermascan_welcome_shown")).toBe("true");
  });

  it("closes when clicking the close (X) button", () => {
    render(<WelcomeModal />);

    const closeBtn = screen.getByRole("button", {
      name: /Close welcome message/i,
    });
    fireEvent.click(closeBtn);

    expect(screen.queryByText(/Welcome to DermaScan AI!/i)).not.toBeInTheDocument();
    expect(sessionStorage.getItem("dermascan_welcome_shown")).toBe("true");
  });

  it("does not display if sessionStorage already has dermascan_welcome_shown = true", () => {
    sessionStorage.setItem("dermascan_welcome_shown", "true");
    render(<WelcomeModal />);

    expect(screen.queryByText(/Welcome to DermaScan AI!/i)).not.toBeInTheDocument();
  });
});