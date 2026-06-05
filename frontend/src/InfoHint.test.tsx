import { render, screen } from "@testing-library/react";
import { InfoHint } from "./InfoHint";

describe("InfoHint", () => {
  it("exposes its text via aria-label and native title", () => {
    render(<InfoHint text="hello" />);
    const hint = screen.getByLabelText("hello");
    expect(hint).toBeInTheDocument();
    expect(hint).toHaveAttribute("title", "hello");
  });
});
