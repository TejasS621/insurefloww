import { useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { Skeleton } from "../../components/ui/Skeleton";
import { StatCard } from "../../components/ui/StatCard";
import { StatusBadge } from "../../components/ui/StatusBadge";
import type { ApplicationSummary, PolicySummary, TicketSummary } from "../../services/api/customer";
import { formatCurrencyINR } from "../../utils/formatters";

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

type DashboardTab = "policies" | "transactions" | "tickets";

interface CustomerDashboardScreenProps {
  customerDisplayName: string;
  applicationsState: {
    loading: boolean;
    error?: string;
    data: ApplicationSummary[];
    onRetry: () => void;
  };
  policiesState: {
    loading: boolean;
    error?: string;
    data: PolicySummary[];
    onRetry: () => void;
  };
  ticketsState: {
    loading: boolean;
    error?: string;
    data: TicketSummary[];
    onRetry: () => void;
  };
  onOpenSupport: () => void;
  onDownloadPolicy: (policyNumber: string) => Promise<void>;
  onViewReceipt: (reference: string) => Promise<void>;
}

/**
 * CustomerDashboardScreen loads each section independently and tolerates partial failures.
 * Policies, applications, and tickets each keep their own loading, success, and error state.
 */
export function CustomerDashboardScreen({
  customerDisplayName,
  applicationsState,
  policiesState,
  ticketsState,
  onOpenSupport,
  onDownloadPolicy,
  onViewReceipt,
}: CustomerDashboardScreenProps) {
  const [activeTab, setActiveTab] = useState<DashboardTab>("policies");
  const activePolicy = policiesState.data[0] ?? null;
  const applicationSummary = applicationsState.data[0] ?? null;

  const dashboardStats = useMemo(
    () => [
      {
        label: "Total Coverage",
        value: formatCurrencyINR(
          policiesState.data.reduce((total, policy) => total + (policy.coverage_amount ?? 0), 0),
        ),
        variant: "stat-1" as const,
      },
      {
        label: "Active Policies",
        value: String(policiesState.data.length),
        variant: "stat-2" as const,
      },
      {
        label: "Next Renewal",
        value: activePolicy?.end_date ? new Date(activePolicy.end_date).toLocaleDateString("en-IN") : "N/A",
        variant: "stat-3" as const,
      },
      {
        label: "Tickets Open",
        value: String(ticketsState.data.length),
        variant: "stat-4" as const,
      },
    ],
    [activePolicy?.end_date, policiesState.data, ticketsState.data.length],
  );

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <h2>
            Welcome back, {applicationSummary?.personal_details.first_name ?? customerDisplayName}
          </h2>
          <p className="if-inline-subtitle">{new Date().toLocaleDateString("en-IN", { dateStyle: "long" })}</p>
        </div>
      </section>

      {policiesState.loading ? (
        <Skeleton height={168} />
      ) : policiesState.error ? (
        <ErrorCard message={policiesState.error} onRetry={policiesState.onRetry} />
      ) : activePolicy ? (
        <section className="if-active-policy-card">
          <div>
            <p className="if-policy-ref">{activePolicy.policy_number}</p>
            <h3>{activePolicy.transaction_reference ?? "Policy"} | Active cover</h3>
            <p className="if-active-policy-meta">
              Coverage: {formatCurrencyINR(activePolicy.coverage_amount)} | Valid till:{" "}
              {activePolicy.end_date ? new Date(activePolicy.end_date).toLocaleDateString("en-IN") : "N/A"}
            </p>
          </div>
          <div className="if-active-policy-actions">
            <StatusBadge status="issued">Policy Issued</StatusBadge>
            <div className="if-active-policy-buttons">
              <Button
                className="if-button-inverse"
                onClick={() => void onDownloadPolicy(activePolicy.policy_number)}
                variant="ghost"
              >
                Download Policy
              </Button>
              <Button
                className="if-button-inverse"
                onClick={() => void onViewReceipt(activePolicy.payment_reference ?? activePolicy.policy_number)}
                variant="ghost"
              >
                View Receipt
              </Button>
            </div>
          </div>
        </section>
      ) : (
        <EmptyState
          title="No Active Policies"
          description="It looks like you don't have any active insurance policies. Explore plans to get started."
          action={<Button onClick={() => window.location.hash = "#/"}>Explore Plans</Button>}
        />
      )}

      <section className="if-dashboard-stats">
        {dashboardStats.map((item) => (
          <StatCard key={item.label} label={item.label} value={item.value} variant={item.variant} />
        ))}
      </section>

      <section className="if-surface-card">
        <div className="if-tab-row">
          {[
            { label: "Policies", value: "policies" },
            { label: "Transactions", value: "transactions" },
            { label: "Tickets", value: "tickets" },
          ].map((tab) => (
            <button
              className={`if-tab-button ${activeTab === tab.value ? "is-active" : ""}`}
              key={tab.value}
              onClick={() => setActiveTab(tab.value as DashboardTab)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "policies" ? (
          policiesState.loading ? (
            <div className="if-skeleton-stack">
              <Skeleton height={56} />
              <Skeleton height={56} />
            </div>
          ) : policiesState.error ? (
            <ErrorCard message={policiesState.error} onRetry={policiesState.onRetry} />
          ) : policiesState.data.length === 0 ? (
            <EmptyState
              title="No Policies Found"
              description="You don't have any policies registered with this account."
              action={<Button onClick={() => window.location.hash = "#/"}>Explore Plans</Button>}
            />
          ) : (
            <div className="if-table-wrap">
              <table className="if-data-table">
                <thead>
                  <tr>
                    <th>Policy No.</th>
                    <th>Type</th>
                    <th>Premium</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {policiesState.data.map((policy) => (
                    <tr key={policy.policy_number}>
                      <td className="if-mono">{policy.policy_number}</td>
                      <td>{policy.transaction_reference ?? "Policy"}</td>
                      <td>{formatCurrencyINR(policy.premium_amount)}</td>
                      <td>
                        <StatusBadge status="issued">{policy.policy_status}</StatusBadge>
                      </td>
                      <td>
                        <Button onClick={() => void onDownloadPolicy(policy.policy_number)} variant="ghost">
                          Download
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : null}

        {activeTab === "transactions" ? (
          applicationsState.loading ? (
            <div className="if-skeleton-stack">
              <Skeleton height={56} />
              <Skeleton height={56} />
            </div>
          ) : applicationsState.error ? (
            <ErrorCard message={applicationsState.error} onRetry={applicationsState.onRetry} />
          ) : applicationsState.data.length === 0 ? (
            <EmptyState
              title="No Transactions Found"
              description="Your transaction and payment history is empty."
            />
          ) : (
            <div className="if-table-wrap">
              <table className="if-data-table">
                <thead>
                  <tr>
                    <th>Ref No.</th>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {applicationsState.data.map((application) => (
                    <tr key={application.application_reference}>
                      <td className="if-mono">{application.transaction_reference ?? application.application_reference}</td>
                      <td>{new Date(application.created_at).toLocaleDateString("en-IN")}</td>
                      <td>{formatCurrencyINR(application.coverage_details.coverage_amount)}</td>
                      <td>
                        <StatusBadge status="processing">{application.application_status}</StatusBadge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : null}

        {activeTab === "tickets" ? (
          ticketsState.loading ? (
            <div className="if-skeleton-stack">
              <Skeleton height={72} />
              <Skeleton height={72} />
            </div>
          ) : ticketsState.error ? (
            <ErrorCard message={ticketsState.error} onRetry={ticketsState.onRetry} />
          ) : ticketsState.data.length === 0 ? (
            <EmptyState
              title="No Tickets Open"
              description="You don't have any support tickets raised. If you need help, raise a ticket below."
              action={<Button onClick={onOpenSupport}>Raise Ticket</Button>}
            />
          ) : (
            <div className="if-ticket-stack">
              {ticketsState.data.map((ticket) => (
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
          )
        ) : null}
      </section>

      <section className="if-mobile-quick-actions">
        <div className="if-mobile-sheet">
          <h3>Quick actions</h3>
          <div className="if-mobile-sheet-actions">
            <Button onClick={onOpenSupport}>Raise Ticket</Button>
            {activePolicy ? (
              <Button onClick={() => void onDownloadPolicy(activePolicy.policy_number)} variant="ghost">
                Download Policy
              </Button>
            ) : null}
            {activePolicy?.payment_reference ? (
              <Button onClick={() => void onViewReceipt(activePolicy.payment_reference ?? "")} variant="ghost">
                View Receipt
              </Button>
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}
