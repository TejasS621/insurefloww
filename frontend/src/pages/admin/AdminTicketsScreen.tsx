import { useState } from "react";

import { Button } from "../../components/ui/Button";
import { Drawer } from "../../components/ui/Drawer";
import { SelectField } from "../../components/ui/SelectField";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { TextareaField } from "../../components/ui/TextareaField";

/**
 * AdminTicketsScreen presents operational ticket handling in a card layout.
 * It supports assignment, status management, and inline response drafting via a drawer.
 */
export function AdminTicketsScreen() {
  const [activeTab, setActiveTab] = useState("all");
  const [selectedTicket, setSelectedTicket] = useState<string | null>("TKT-20260613-101");

  return (
    <div className="if-screen-stack">
      <section className="if-pill-group">
        {["all", "open", "in progress", "resolved"].map((tab) => (
          <button
            key={tab}
            className={`if-pill ${activeTab === tab ? "is-active" : ""}`}
            onClick={() => setActiveTab(tab)}
            type="button"
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </section>

      <section className="if-ticket-stack">
        {[
          {
            id: "TKT-20260613-101",
            priority: "high",
            subject: "Payment confirmation missing",
            customer: "Tejas Shah",
            mobile: "7778889997",
            category: "Payment",
            status: "Open",
            updated: "2 hours ago",
          },
          {
            id: "TKT-20260612-078",
            priority: "medium",
            subject: "Need policy endorsement",
            customer: "Riya Nair",
            mobile: "8887776665",
            category: "Policy",
            status: "In Progress",
            updated: "5 hours ago",
          },
        ].map((ticket) => (
          <article className="if-admin-ticket-card" key={ticket.id}>
            <div className={`if-priority-rail is-${ticket.priority}`} />
            <div className="if-admin-ticket-main">
              <div>
                <p className="if-mono">{ticket.id}</p>
                <h3>{ticket.subject}</h3>
                <p className="if-inline-subtitle">
                  {ticket.customer} | {ticket.mobile}
                </p>
              </div>
              <div className="if-admin-ticket-meta">
                <StatusBadge status="processing">{ticket.category}</StatusBadge>
                <StatusBadge status={ticket.status === "Open" ? "pending" : "processing"}>
                  {ticket.status}
                </StatusBadge>
                <span>{ticket.updated}</span>
              </div>
              <div className="if-table-action-row">
                <Button onClick={() => setSelectedTicket(ticket.id)} variant="ghost">
                  Assign
                </Button>
                <Button onClick={() => setSelectedTicket(ticket.id)} variant="ghost">
                  Update Status
                </Button>
              </div>
            </div>
          </article>
        ))}
      </section>

      {selectedTicket ? (
        <Drawer title="Ticket detail" width="wide">
          <div className="if-detail-stack">
            <div className="if-detail-row">
              <span>Ticket</span>
              <strong className="if-mono">{selectedTicket}</strong>
            </div>
            <div className="if-detail-row">
              <span>Customer</span>
              <strong>Tejas Shah | 7778889997</strong>
            </div>
            <div className="if-detail-row">
              <span>Status</span>
              <StatusBadge status="pending">Open</StatusBadge>
            </div>
            <blockquote className="if-ticket-quote">
              I completed the payment successfully, but the dashboard still shows payment pending.
            </blockquote>
            <TextareaField label="Admin response" placeholder="Type your response" rows={5} />
            <div className="if-table-action-row">
              <Button>Send Response</Button>
            </div>
            <div className="if-form-grid">
              <SelectField
                label="Status update"
                options={[
                  { label: "Open", value: "open" },
                  { label: "In Progress", value: "in_progress" },
                  { label: "Resolved", value: "resolved" },
                ]}
              />
              <div className="if-drawer-save">
                <Button>Save</Button>
              </div>
            </div>
            <div className="if-modal-footer">
              <Button onClick={() => setSelectedTicket(null)} variant="ghost">
                Close
              </Button>
            </div>
          </div>
        </Drawer>
      ) : null}
    </div>
  );
}
