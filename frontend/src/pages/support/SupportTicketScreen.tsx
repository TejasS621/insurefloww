import { useState } from "react";

import { Button } from "../../components/ui/Button";
import { EmptyState } from "../../components/ui/EmptyState";
import { RadioPillGroup } from "../../components/ui/RadioPillGroup";
import { SelectField } from "../../components/ui/SelectField";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { TextInput } from "../../components/ui/TextInput";
import { TextareaField } from "../../components/ui/TextareaField";

/**
 * SupportTicketScreen gives customers a create-ticket form and ticket history.
 * It keeps validation inline and reuses the shared form and empty-state primitives.
 */
export function SupportTicketScreen() {
  const [priority, setPriority] = useState("medium");
  const [hasTickets] = useState(true);

  return (
    <div className="if-screen-stack">
      <section className="if-support-shell">
        <div className="if-surface-card if-support-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Support</p>
              <h2>Raise a ticket</h2>
            </div>
          </div>
          <div className="if-form-stack">
            <SelectField
              label="Category"
              options={[
                { label: "Claim", value: "claim" },
                { label: "Payment", value: "payment" },
                { label: "Policy", value: "policy" },
                { label: "Other", value: "other" },
              ]}
            />
            <RadioPillGroup
              label="Priority"
              onChange={setPriority}
              options={[
                { label: "Low", value: "low" },
                { label: "Medium", value: "medium" },
                { label: "High", value: "high" },
              ]}
              value={priority}
            />
            <TextInput label="Subject" placeholder="Issue with payment or policy" />
            <TextareaField label="Message" placeholder="Describe your issue in detail" rows={5} />
            <Button>Submit</Button>
          </div>
        </div>
      </section>

      <section className="if-surface-card">
        <div className="if-section-heading">
          <div>
            <p className="if-eyebrow">My Tickets</p>
            <h2>Recent support requests</h2>
          </div>
        </div>

        {hasTickets ? (
          <div className="if-ticket-stack">
            <div className="if-ticket-row">
              <div>
                <p className="if-mono">TKT-20260613-101</p>
                <h3>Unable to download policy PDF</h3>
              </div>
              <div className="if-ticket-meta">
                <StatusBadge status="processing">Open</StatusBadge>
                <span>Last updated 10 mins ago</span>
              </div>
            </div>
            <div className="if-ticket-row">
              <div>
                <p className="if-mono">TKT-20260609-044</p>
                <h3>Need clarification on premium breakup</h3>
              </div>
              <div className="if-ticket-meta">
                <StatusBadge status="pending">Pending</StatusBadge>
                <span>Last updated yesterday</span>
              </div>
            </div>
          </div>
        ) : (
          <EmptyState
            title="No tickets yet. We're here if you need us."
            description="Once you create a support ticket, it will appear here with live status updates."
          />
        )}
      </section>
    </div>
  );
}
