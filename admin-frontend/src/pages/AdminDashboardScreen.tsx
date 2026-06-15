import { ArrowRight, Blocks, CircleDot, ClipboardList, ListOrdered, Shield, UserRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { ErrorCard } from "../components/ui/ErrorCard";
import { Skeleton } from "../components/ui/Skeleton";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge } from "../components/ui/StatusBadge";
import { adminApi, type AdminDashboardStats } from "../services/api/admin";
import { normalizeApiError } from "../utils/apiErrors";
import { formatCurrencyINR } from "../utils/formatters";

interface AdminDashboardScreenProps {
  onNavigate: (screen: "dashboard" | "brokers" | "providers" | "transactions" | "policies" | "payments" | "tickets") => void;
}

/**
 * AdminDashboardScreen fetches operational stats and recent transactions on mount.
 * Each section keeps its own loading and error state so one failure does not block the page.
 */
export function AdminDashboardScreen({ onNavigate }: AdminDashboardScreenProps) {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState("");
  const [transactions, setTransactions] = useState<Array<Record<string, string | number>>>([]);
  const [transactionsLoading, setTransactionsLoading] = useState(true);
  const [transactionsError, setTransactionsError] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "PENDING" | "SUCCESS" | "FAILED">("ALL");

  const loadDashboardStats = async () => {
    setStatsLoading(true);
    setStatsError("");
    try {
      const statsResult = await adminApi.getDashboard();
      setStats(statsResult);
    } catch (error) {
      setStatsError(normalizeApiError(error).message);
    } finally {
      setStatsLoading(false);
    }
  };

  const fetchTransactions = async (status: string) => {
    setTransactionsLoading(true);
    setTransactionsError("");
    try {
      const transactionParams = new URLSearchParams({
        page: "1",
        limit: "5",
        status: status,
      });
      const result = await adminApi.listTransactions(transactionParams);
      setTransactions(result.items);
    } catch (error) {
      setTransactionsError(normalizeApiError(error).message);
    } finally {
      setTransactionsLoading(false);
    }
  };

  useEffect(() => {
    void loadDashboardStats();
  }, []);

  useEffect(() => {
    void fetchTransactions(statusFilter);
  }, [statusFilter]);

  const quickLinks = useMemo(
    () => [
      { label: "Manage Brokers", icon: Shield, screen: "brokers" as const },
      { label: "Manage Providers", icon: Blocks, screen: "providers" as const },
      { label: "View Tickets", icon: ClipboardList, screen: "tickets" as const },
      { label: "Audit Logs", icon: ListOrdered, screen: "transactions" as const },
      { label: "Manage Customers", icon: UserRound, screen: "dashboard" as const },
    ],
    [],
  );

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
            <ErrorCard message={statsError} onRetry={() => void loadDashboardStats()} />
          </div>
        ) : (
          <>
            <StatCard label="Total Applications" value={String(stats?.total_applications ?? 0)} variant="stat-1" />
            <StatCard label="Active Policies" value={String(stats?.total_policies ?? 0)} variant="stat-2" />
            <StatCard label="Revenue Today" value={formatCurrencyINR(485000)} variant="stat-3" />
            <StatCard label="Pending Payments" value={String(stats?.pending_underwriting_reviews ?? 0)} variant="stat-4" />
          </>
        )}
      </section>

      <section className="if-admin-dashboard-grid">
        <div className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Transactions</p>
              <h2>Recent transactions</h2>
            </div>
            <button
              className="if-link-button"
              onClick={() => onNavigate("transactions")}
              style={{ color: "var(--if-violet)", display: "flex", alignItems: "center", gap: "4px" }}
              type="button"
            >
              View all →
            </button>
          </div>

          <div className="if-pill-group" style={{ marginBottom: "var(--space-4)" }}>
            {(["ALL", "PENDING", "SUCCESS", "FAILED"] as const).map((filter) => (
              <button
                key={filter}
                className={`if-pill ${statusFilter === filter ? "is-active" : ""}`}
                onClick={() => setStatusFilter(filter)}
                style={
                  statusFilter === filter
                    ? {
                        background: "rgba(124, 58, 237, 0.15)",
                        color: "var(--if-text-1)",
                        borderColor: "var(--if-violet)",
                      }
                    : undefined
                }
                type="button"
              >
                {filter.charAt(0) + filter.slice(1).toLowerCase()}
              </button>
            ))}
          </div>

          {transactionsLoading ? (
            <div className="if-skeleton-stack">
              <Skeleton height={56} />
              <Skeleton height={56} />
              <Skeleton height={56} />
            </div>
          ) : transactionsError ? (
            <ErrorCard message={transactionsError} onRetry={() => void fetchTransactions(statusFilter)} />
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
                          <StatusBadge
                            status={
                              String(transaction.status).toUpperCase() === "SUCCESS"
                                ? "issued"
                                : String(transaction.status).toUpperCase() === "PENDING"
                                  ? "pending"
                                  : "failed"
                            }
                          >
                            {String(transaction.status ?? "PROCESSING")}
                          </StatusBadge>
                        </td>
                        <td>{String(transaction.date ?? "N/A")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
            <div className="if-link-list" style={{ display: "grid", gap: 0 }}>
              {quickLinks.map((item) => (
                <button
                  className="if-link-row"
                  key={item.label}
                  onClick={() => onNavigate(item.screen)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "12px 16px",
                    background: "transparent",
                    border: "none",
                    borderBottom: "1px solid var(--if-border)",
                    cursor: "pointer",
                  }}
                  type="button"
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <item.icon size={20} style={{ color: "var(--if-violet)" }} />
                    <span style={{ color: "var(--if-text-1)", fontWeight: "500" }}>{item.label}</span>
                  </div>
                  <ArrowRight size={16} style={{ color: "var(--if-text-2)" }} />
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
            <div className="if-status-stack" style={{ display: "grid", gap: "12px" }}>
              <div className="if-system-status-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ color: "var(--if-text-1)" }}>Provider Backend</span>
                <span className="if-system-state" style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--if-text-2)" }}>
                  <CircleDot size={10} style={{ color: "#10B981" }} />
                  Online
                </span>
              </div>
              <div className="if-system-status-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ color: "var(--if-text-1)" }}>Payment Gateway</span>
                <span className="if-system-state" style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--if-text-2)" }}>
                  <CircleDot size={10} style={{ color: "#10B981" }} />
                  Online
                </span>
              </div>
              <div className="if-system-status-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ color: "var(--if-text-1)" }}>Webhook Retry</span>
                <span className="if-system-state" style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--if-text-2)" }}>
                  <CircleDot size={10} style={{ color: "#F59E0B" }} />
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
