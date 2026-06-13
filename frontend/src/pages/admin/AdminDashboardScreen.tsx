import { ArrowRight, CircleDot } from "lucide-react";
import { useEffect, useState } from "react";

import { ErrorCard } from "../../components/ui/ErrorCard";
import { Skeleton } from "../../components/ui/Skeleton";
import { StatCard } from "../../components/ui/StatCard";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { adminApi, type AdminDashboardStats } from "../../services/api/admin";
import { normalizeApiError } from "../../utils/apiErrors";
import { formatCurrencyINR } from "../../utils/formatters";

/**
 * AdminDashboardScreen fetches operational stats and recent transactions on mount.
 * Each section keeps its own loading and error state so one failure does not block the page.
 */
export function AdminDashboardScreen() {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState("");
  const [transactions, setTransactions] = useState<Array<Record<string, string | number>>>([]);
  const [transactionsLoading, setTransactionsLoading] = useState(true);
  const [transactionsError, setTransactionsError] = useState("");

  const loadDashboard = async () => {
    setStatsLoading(true);
    setTransactionsLoading(true);
    setStatsError("");
    setTransactionsError("");

    const transactionParams = new URLSearchParams({
      page: "1",
      limit: "5",
      status: "ALL",
    });

    const [statsResult, transactionsResult] = await Promise.allSettled([
      adminApi.getDashboard(),
      adminApi.listTransactions(transactionParams),
    ]);

    if (statsResult.status === "fulfilled") {
      setStats(statsResult.value);
    } else {
      setStatsError(normalizeApiError(statsResult.reason).message);
    }
    setStatsLoading(false);

    if (transactionsResult.status === "fulfilled") {
      setTransactions(transactionsResult.value.items);
    } else {
      setTransactionsError(normalizeApiError(transactionsResult.reason).message);
    }
    setTransactionsLoading(false);
  };

  useEffect(() => {
    void loadDashboard();
  }, []);

  return (
    <div className="if-screen-stack">
      <section className="if-grid if-admin-metric-grid">
        {statsLoading ? (
          <>
            <Skeleton height={128} />
            <Skeleton height={128} />
            <Skeleton height={128} />
            <Skeleton height={128} />
          </>
        ) : statsError ? (
          <div className="if-form-grid-span">
            <ErrorCard message={statsError} onRetry={() => void loadDashboard()} />
          </div>
        ) : (
          <>
            <StatCard label="Total Applications" value={String(stats?.total_applications ?? 0)} variant="navy" />
            <StatCard label="Active Policies" value={String(stats?.total_policies ?? 0)} />
            <StatCard label="Revenue Today" value={formatCurrencyINR(485000)} variant="navy" />
            <article className="if-stat-card if-stat-card-warning">
              <p className="if-stat-label">Pending Payments</p>
              <p className="if-stat-value">{stats?.pending_underwriting_reviews ?? 0}</p>
            </article>
          </>
        )}
      </section>

      <section className="if-admin-dashboard-grid">
        <div className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Transactions</p>
              <h2>Recent Transactions</h2>
            </div>
          </div>
          {transactionsLoading ? (
            <div className="if-skeleton-stack">
              <Skeleton height={56} />
              <Skeleton height={56} />
              <Skeleton height={56} />
            </div>
          ) : transactionsError ? (
            <ErrorCard message={transactionsError} onRetry={() => void loadDashboard()} />
          ) : (
            <>
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
                    {transactions.map((transaction, index) => (
                      <tr key={`${transaction.transaction_reference ?? index}`}>
                        <td className="if-mono">{String(transaction.transaction_reference ?? "N/A")}</td>
                        <td>{String(transaction.customer_name ?? "Customer")}</td>
                        <td>{String(transaction.insurance_type ?? "Policy")}</td>
                        <td>{formatCurrencyINR(Number(transaction.amount ?? 0))}</td>
                        <td>
                          <StatusBadge status="processing">
                            {String(transaction.status ?? "PROCESSING")}
                          </StatusBadge>
                        </td>
                        <td>{String(transaction.date ?? "N/A")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="if-pagination-footer">
                <button className="if-link-button" type="button">
                  Previous
                </button>
                <span>Page 1</span>
                <button className="if-link-button" type="button">
                  Next
                </button>
              </div>
            </>
          )}
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
                  <CircleDot size={10} />
                  2 pending
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
