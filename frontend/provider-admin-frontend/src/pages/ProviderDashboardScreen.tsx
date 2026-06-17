import { useEffect, useMemo, useState } from "react";

import { Button } from "../components/ui/Button";
import { ErrorCard } from "../components/ui/ErrorCard";
import { Skeleton } from "../components/ui/Skeleton";
import { StatCard } from "../components/ui/StatCard";
import { providerAdminApi, type ProviderBrokerSummary, type ProviderSyncStatusResponse } from "../services/api/providerAdmin";
import { providerRegistryApi, type ProviderRegistrySummary } from "../services/api/providerRegistry";
import { normalizeApiError } from "../utils/apiErrors";

interface ProviderDashboardScreenProps {
  onNavigate: (screen: "providers" | "brokers" | "sync") => void;
}

export function ProviderDashboardScreen({ onNavigate }: ProviderDashboardScreenProps) {
  const [providers, setProviders] = useState<ProviderRegistrySummary[]>([]);
  const [brokers, setBrokers] = useState<ProviderBrokerSummary[]>([]);
  const [syncRetries, setSyncRetries] = useState<ProviderSyncStatusResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = async () => {
    setLoading(true);
    setError("");
    try {
      const [providerRecords, brokerRecords, retryRecords] = await Promise.all([
        providerRegistryApi.listProviders(),
        providerAdminApi.listBrokers(),
        providerAdminApi.listSyncRetries(),
      ]);
      setProviders(providerRecords);
      setBrokers(brokerRecords);
      setSyncRetries(retryRecords);
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadDashboard();
  }, []);

  const summary = useMemo(() => {
    const activeProviders = providers.filter((provider) => provider.status === "ACTIVE").length;
    const activeBrokers = brokers.filter((broker) => broker.status === "ACTIVE").length;
    const pendingRetries = syncRetries.filter((record) => record.status !== "SUCCESS").length;
    const latestEvents = syncRetries.slice(0, 5);

    return {
      totalProviders: providers.length,
      activeProviders,
      activeBrokers,
      pendingRetries,
      totalBrokers: brokers.length,
      latestEvents,
    };
  }, [brokers, providers, syncRetries]);

  if (error) {
    return <ErrorCard message={error} onRetry={() => void loadDashboard()} />;
  }

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Provider Console</p>
          <h2>Operational overview</h2>
        </div>
        <Button onClick={() => void loadDashboard()} variant="ghost">
          Refresh
        </Button>
      </section>

      <section className="if-stats-grid">
        {loading ? (
          <>
            <Skeleton height={156} />
            <Skeleton height={156} />
            <Skeleton height={156} />
            <Skeleton height={156} />
          </>
        ) : (
          <>
            <StatCard label="Registered Providers" value={String(summary.totalProviders)} variant="stat-1" />
            <StatCard label="Active Providers" value={String(summary.activeProviders)} variant="stat-2" />
            <StatCard label="Registered Brokers" value={String(summary.totalBrokers)} variant="stat-3" />
            <StatCard label="Pending Sync Retries" value={String(summary.pendingRetries)} variant="stat-3" />
            <StatCard label="Active Brokers" value={String(summary.activeBrokers)} variant="navy" />
          </>
        )}
      </section>

      <section className="if-grid-two">
        <article className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Latest Sync Events</p>
              <h3>Recent provider-to-main sync activity</h3>
            </div>
            <Button onClick={() => onNavigate("sync")} variant="ghost">
              Open Sync Center
            </Button>
          </div>
          {loading ? (
            <div className="if-skeleton-stack">
              <Skeleton height={56} />
              <Skeleton height={56} />
              <Skeleton height={56} />
            </div>
          ) : summary.latestEvents.length === 0 ? (
            <p className="if-inline-subtitle">No sync events have been recorded yet.</p>
          ) : (
            <div className="if-list-stack">
              {summary.latestEvents.map((event) => (
                <div className="if-list-row" key={`${event.event_type}-${event.updated_at}-${event.main_transaction_reference}`}>
                  <div>
                    <p className="if-list-title">{event.event_type}</p>
                    <p className="if-inline-subtitle if-mono">{event.main_transaction_reference}</p>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <p className="if-list-title">{event.status}</p>
                    <p className="if-inline-subtitle">{new Date(event.updated_at).toLocaleString("en-IN")}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Quick Actions</p>
              <h3>Provider admin shortcuts</h3>
            </div>
          </div>
          <div className="if-form-stack">
            <Button onClick={() => onNavigate("providers")} variant="ghost">
              Manage Providers
            </Button>
            <Button onClick={() => onNavigate("brokers")}>Manage Brokers</Button>
            <Button onClick={() => onNavigate("sync")} variant="ghost">
              Review Sync Retries
            </Button>
          </div>
        </article>
      </section>
    </div>
  );
}
