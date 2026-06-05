import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { ClientsView } from "./ClientsView";

// Mock the API layer so the component renders without a real backend.
vi.mock("./api", () => ({
  getClients: vi.fn().mockResolvedValue([
    { sys_id: "c1", name: "Acme Corp", short_code: "ACME", status: "active" },
  ]),
  createClient: vi.fn(),
  updateClient: vi.fn(),
}));

describe("ClientsView", () => {
  it("lists clients from the API and offers an Add form", async () => {
    render(<ClientsView onOpen={() => {}} />);
    expect(await screen.findByText(/Acme Corp/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add client/i })).toBeInTheDocument();
  });
});
