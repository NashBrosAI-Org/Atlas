import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { Sidebar } from "./Sidebar";

describe("Sidebar", () => {
  it("app name links home and opens Now", () => {
    const onNavigate = vi.fn();
    render(<Sidebar current="help" onNavigate={onNavigate} onCapture={() => {}} />);
    const home = screen.getByRole("link", { name: "Atlas" });
    expect(home).toHaveAttribute("href", "/");
    fireEvent.click(home);
    expect(onNavigate).toHaveBeenCalledWith("now");
  });
});
