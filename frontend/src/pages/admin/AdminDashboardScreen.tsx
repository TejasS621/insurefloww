import { ArrowRight, CircleDot } from "lucide-react";
import { useState } from "react";

import { StatCard } from "../../components/ui/StatCard";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { formatCurrencyINR } from "../../utils/formatters";

/**
 * AdminDashboardScreen gives operations users a high-level control center.
 * It combines top metrics, recent financial activity, links, and system health.
 */
export function AdminDashboardScreen() {
  const [transactionFilter, setTransactionFilter] = useState("all");

  return (
    <div className="if-screen-stack">
      <section className="if-grid if-admin-metric-grid">
        <StatCard label="Total Applications" value="1,248" variant="navy" />
        <StatCard label="Active Policies" value="867" />
        <StatCard label="Revenue Today" value={formatCurrencyINR(485000)} variant="navy" />
        <article className="if-stat-card if-stat-card-warning">
          <p className="if-stat-label">Pending Payments</p>
          <p className="if-stat-value">42</p>
        </article>
      </section>

      <section className="if-admin-dashboard-grid">
        <div className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Transactions</p>
              <h2>Recent Transactions</h2>
            </div>
          </div>
          <div className="if-pill-group if-admin-filter-row">
            {["all", "pending", "success", "failed"].map((item) => (
              <button
                key={item}
                className={`if-pill ${transactionFilter === item ? "is-active" : ""}`}
                onClick={() => setTransactionFilter(item)}
                type="button"
              >
                {item.charAt(0).toUpperCase() + item.slice(1)}
              </button>
            ))}
          </div>
          <div className="if-table-wrap">
            <table className="if-data-table">
              <thead>
                <tr>
                  <th>Ref No.</th>
                  <th>Customer</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="if-mono">TXN-HLT-20260613-AF21</td>
                  <td>Tejas Shah</td>
                  <td>Health</td>
                  <td>{formatCurrencyINR(27258)}</td>
                  <td>
                    <StatusBadge status="issued">Success</StatusBadge>
                  </td>
                  <td>13 Jun 2026</td>
                </tr>
                <tr>
                  <td className="if-mono">TXN-LIF-20260613-PQ88</td>
                  <td>Riya Nair</td>
                  <td>Life</td>
                  <td>{formatCurrencyINR(39120)}</td>
                  <td>
                    <StatusBadge status="pending">Pending</StatusBadge>
                  </td>
                  <td>13 Jun 2026</td>
                </tr>
                <tr>
                  <td className="if-mono">TXN-MTR-20260612-RS52</td>
                  <td>Aman Verma</td>
                  <td>Vehicle</td>
                  <td>{formatCurrencyINR(18940)}</td>
                  <td>
                    <StatusBadge status="failed">Failed</StatusBadge>
                  </td>
                  <td>12 Jun 2026</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="if-pagination-footer">
            <button className="if-link-button" type="button">
              Previous
            </button>
            <span>Page 1 of 18</span>
            <button className="if-link-button" type="button">
              Next
            </button>
          </div>
        </div>

        <div className="if-admin-side-stack">
          <div className="if-surface-card">
            <div className="if-section-heading">
              <div>
                <p className="if-eyebrow">Quick Links</p>
                <h2>Operations shortcuts</h2>
              </div>
            </div>
            <div className="if-link-list">
              {["Manage Brokers", "View All Tickets", "Audit Logs", "Manage Customers"].map((item) => (
                <button className="if-link-row" key={item} type="button">
                  <span>{item}</span>
                  <ArrowRight size={16} />
                </button>
              ))}
            </div>
          </div>

          <div className="if-surface-card">
            <div className="if-section-heading">
              <div>
                <p className="if-eyebrow">System Status</p>
                <h2>Platform health</h2>
              </div>
            </div>
            <div className="if-status-stack">
              <div className="if-system-status-row">
                <span>Provider Backend</span>
                <span className="if-system-state is-green">
                  <CircleDot size={10} />
                  Online
                </span>
              </div>
              <div className="if-system-status-row">
                <span>Payment Gateway</span>
                <span className="if-system-state is-green">
                  <CircleDot size={10} />
                  Online
                </span>
              </div>
              <div className="if-system-status-row">
                <span>Webhook Retry</span>
                <span className="if-system-state is-amber">
                  <CircleDot size={10} />2 pending
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
