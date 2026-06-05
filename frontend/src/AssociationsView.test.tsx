import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { AssociationsView } from "./AssociationsView";

vi.mock("./api", () => ({
  getAssociations: vi.fn().mockResolvedValue({
    emails: [
      { type: "email", sys_id: "e1", label: "Renewal terms", who: "joe@acme.com", client: "c1", client_name: "Acme Corp" },
    ],
    meetings: [],
  }),
  getClients: vi.fn().mockResolvedValue([
    { sys_id: "c1", name: "Acme Corp", status: "active" },
  ]),
  reassignAssociation: vi.fn().mockResolvedValue({}),
}));

describe("AssociationsView", () => {
  it("renders an email row with its label and assigned client name", async () => {
    render(<AssociationsView onOpenClient={() => {}} />);
    expect(await screen.findByText(/Renewal terms/)).toBeInTheDocument();
    expect(screen.getByText(/joe@acme.com/)).toBeInTheDocument();
    expect(await screen.findByDisplayValue(/Acme Corp/)).toBeInTheDocument();
  });
});
