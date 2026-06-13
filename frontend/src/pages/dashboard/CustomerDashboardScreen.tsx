import { useState } from "react";

import { Button } from "../../components/ui/Button";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { formatCurrencyINR } from "../../utils/formatters";

type DashboardTab = "policies" | "transactions" | "tickets";

interface CustomerDashboardScreenProps {
  onOpenSupport: () => void;
}

/**
 * CustomerDashboardScreen surfaces active policy details, stats, and self-service tabs.
 * It is the signed-in customer home base after policy issuance and payment completion.
 */
export function CustomerDashboardScreen({ onOpenSupport }: CustomerDashboardScreenProps) {
  const [activeTab, setActiveTab] = useState<DashboardTab>("policies");

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <h2>Welcome back, Tejas</h2>
          <p className="if-inline-subtitle">13 June 2026</p>
        </div>
      </section>

      <section className="if-active-policy-card">
        <div>
          <p className="if-policy-ref">POL-HLT-20260613-AX18</p>
          <h3>Health Insurance | Nova Life</h3>
          <p className="if-active-policy-meta">
            Coverage: {formatCurrencyINR(1000000)} | Valid till: 12 Jun 2027
          </p>
        </div>
        <div className="if-active-policy-actions">
          <StatusBadge status="issued">Policy Issued</StatusBadge>
          <div className="if-active-policy-buttons">
            <Button className="if-button-inverse" variant="ghost">
              Download Policy
            </Button>
            <Button className="if-button-inverse" variant="ghost">
              View Receipt
            </Button>
          </div>
        </div>
      </section>

      <section className="if-dashboard-stats">
        <article className="if-mini-stat-card">
          <span>Total Coverage</span>
          <strong>{formatCurrencyINR(1000000)}</strong>
        </article>
        <article className="if-mini-stat-card">
          <span>Active Policies</span>
          <strong>2</strong>
        </article>
        <article className="if-mini-stat-card">
          <span>Next Renewal</span>
          <strong>12 Jun 2027</strong>
        </article>
        <article className="if-mini-stat-card">
          <span>Tickets Open</span>
          <strong>1</strong>
        </article>
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
                <tr>
                  <td className="if-mono">POL-HLT-20260613-AX18</td>
                  <td>Health</td>
                  <td>{formatCurrencyINR(27258)}</td>
                  <td>
                    <StatusBadge status="issued">Issued</StatusBadge>
                  </td>
                  <td>
                    <Button variant="ghost">Download</Button>
                  </td>
                </tr>
                <tr>
                  <td className="if-mono">POL-TRV-20260402-MP77</td>
                  <td>Travel</td>
                  <td>{formatCurrencyINR(12840)}</td>
                  <td>
                    <StatusBadge status="pending">Pending</StatusBadge>
                  </td>
                  <td>
                    <Button variant="ghost">Download</Button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : null}

        {activeTab === "transactions" ? (
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
                <tr>
                  <td className="if-mono">TXN-HLT-20260613-KL4D</td>
                  <td>13 Jun 2026</td>
                  <td>{formatCurrencyINR(27258)}</td>
                  <td>
                    <StatusBadge status="issued">Paid</StatusBadge>
                  </td>
                </tr>
                <tr>
                  <td className="if-mono">TXN-TRV-20260402-QL2A</td>
                  <td>02 Apr 2026</td>
                  <td>{formatCurrencyINR(12840)}</td>
                  <td>
                    <StatusBadge status="failed">Failed</StatusBadge>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : null}

        {activeTab === "tickets" ? (
          <div className="if-ticket-stack">
            <div className="if-ticket-row">
              <div>
                <p className="if-mono">TKT-20260611-017</p>
                <h3>Payment confirmation not reflected</h3>
              </div>
              <div className="if-ticket-meta">
                <StatusBadge status="processing">Open</StatusBadge>
                <span>Last updated 2 hours ago</span>
              </div>
            </div>
            <div className="if-ticket-row">
              <div>
                <p className="if-mono">TKT-20260529-003</p>
                <h3>Need endorsement on policy details</h3>
              </div>
              <div className="if-ticket-meta">
                <StatusBadge status="pending">Pending</StatusBadge>
                <span>Last updated 3 days ago</span>
              </div>
            </div>
          </div>
        ) : null}
      </section>

      <section className="if-mobile-quick-actions">
        <div className="if-mobile-sheet">
          <h3>Quick actions</h3>
          <div className="if-mobile-sheet-actions">
            <Button onClick={onOpenSupport}>Raise Ticket</Button>
            <Button variant="ghost">Download Policy</Button>
            <Button variant="ghost">Contact Support</Button>
          </div>
        </div>
      </section>
    </div>
  );
}
