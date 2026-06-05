import { render, screen } from "@testing-library/react";
import { OrgChart } from "./OrgChart";
import type { Contact } from "./types";

const contacts: Contact[] = [
  { sys_id: "1", name: "Jane Doe", role_title: "VP Engineering", sentiment: "champion" },
  { sys_id: "2", name: "John Roe", role_title: "Procurement", reports_to: "1", sentiment: "neutral" },
];

describe("OrgChart", () => {
  it("renders contacts with names and roles", () => {
    render(<OrgChart contacts={contacts} />);
    expect(screen.getByText(/Jane Doe/)).toBeInTheDocument();
    expect(screen.getByText(/VP Engineering/)).toBeInTheDocument();
    expect(screen.getByText(/John Roe/)).toBeInTheDocument();
  });

  it("shows an empty state when there are no contacts", () => {
    render(<OrgChart contacts={[]} />);
    expect(screen.getByText(/no contacts/i)).toBeInTheDocument();
  });
});
