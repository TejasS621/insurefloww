import { useState } from "react";

import { Button } from "../../components/ui/Button";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { RadioPillGroup } from "../../components/ui/RadioPillGroup";
import { SelectField } from "../../components/ui/SelectField";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { TextInput } from "../../components/ui/TextInput";
import { TextareaField } from "../../components/ui/TextareaField";
import type { TicketSummary } from "../../services/api/customer";

const getDaysElapsed = (updatedAtStr: string) => {
  const updatedAt = new Date(updatedAtStr);
  const now = new Date();
  const oneDay = 24 * 60 * 60 * 1000;
  const diffTime = Math.abs(now.getTime() - updatedAt.getTime());
  const diffDays = Math.floor(diffTime / oneDay);
  if (diffDays === 0) {
    return "today";
  } else if (diffDays === 1) {
    return "1 day ago";
  } else {
    return `${diffDays} days ago`;
  }
};

const getPriorityClass = (priority: string) => {
  switch (priority.toUpperCase()) {
    case "HIGH":
      return "is-high";
    case "MEDIUM":
      return "is-medium";
    case "LOW":
    default:
      return "is-low";
  }
};

interface SupportTicketScreenProps {
  loading: boolean;
  error?: string;
  tickets: TicketSummary[];
  submitError?: string;
  onRetry: () => void;
  onSubmit: (payload: {
    category: string;
    priority: string;
    subject: string;
    message: string;
  }) => Promise<void>;
  isSubmitting: boolean;
}

/**
 * SupportTicketScreen submits customer tickets and renders API-backed ticket history.
 * It preserves inline validation and section-level retry behavior for failed fetches.
 */
export function SupportTicketScreen({
  loading,
  error,
  tickets,
  submitError,
  onRetry,
  onSubmit,
  isSubmitting,
}: SupportTicketScreenProps) {
  const [priority, setPriority] = useState("MEDIUM");
  const [category, setCategory] = useState("GENERAL");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");

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
          {submitError ? <ErrorCard message={submitError} /> : null}
          <div className="if-form-stack">
            <SelectField
              label="Category"
              onChange={(event) => setCategory(event.target.value)}
              options={[
                { label: "Claim", value: "GENERAL" },
                { label: "Payment", value: "PAYMENT" },
                { label: "Policy", value: "POLICY" },
                { label: "Other", value: "TECHNICAL" },
              ]}
              value={category}
            />
            <RadioPillGroup
              label="Priority"
              onChange={setPriority}
              options={[
                { label: "Low", value: "LOW" },
                { label: "Medium", value: "MEDIUM" },
                { label: "High", value: "HIGH" },
              ]}
              value={priority}
            />
            <TextInput
              label="Subject"
              onChange={(event) => setSubject(event.target.value)}
              placeholder="Issue with payment or policy"
              value={subject}
            />
            <TextareaField
              label="Message"
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Describe your issue in detail"
              rows={5}
              value={message}
            />
            <Button
              loading={isSubmitting}
              onClick={() =>
                void onSubmit({
                  category,
                  priority,
                  subject,
                  message,
                })
              }
            >
              Submit
            </Button>
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

        {loading ? (
          <div className="if-skeleton-stack">
            <div className="if-skeleton" style={{ height: 72 }} />
            <div className="if-skeleton" style={{ height: 72 }} />
          </div>
        ) : error ? (
          <ErrorCard message={error} onRetry={onRetry} />
        ) : tickets.length > 0 ? (
          <div className="if-ticket-stack">
            {tickets.map((ticket) => (
              <div className={`if-ticket-row ${getPriorityClass(ticket.priority)}`} key={ticket.ticket_reference}>
                <div>
                  <p className="if-mono">{ticket.ticket_reference}</p>
                  <h3>{ticket.subject}</h3>
                </div>
                <div className="if-ticket-meta">
                  <StatusBadge status="processing">{ticket.status}</StatusBadge>
                  <span>Updated {getDaysElapsed(ticket.updated_at)}</span>
                </div>
              </div>
            ))}
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
