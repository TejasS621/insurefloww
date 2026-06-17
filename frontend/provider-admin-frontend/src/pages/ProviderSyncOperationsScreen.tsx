import { useEffect, useState } from "react";

import { Button } from "../components/ui/Button";
import { ErrorCard } from "../components/ui/ErrorCard";
import { Skeleton } from "../components/ui/Skeleton";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TextInput } from "../components/ui/TextInput";
import {
  providerAdminApi,
  type ProviderSyncStatusResponse,
  type RetryProcessingResponse,
} from "../services/api/providerAdmin";
import { normalizeApiError } from "../utils/apiErrors";

export function ProviderSyncOperationsScreen() {
  const [records, setRecords] = useState<ProviderSyncStatusResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [paymentReference, setPaymentReference] = useState("");
  const [dispatchMessage, setDispatchMessage] = useState("");
  const [processingSummary, setProcessingSummary] = useState<RetryProcessingResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadRetries = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await providerAdminApi.listSyncRetries();
      setRecords(response);
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRetries();
  }, []);

  const handleDispatch = async () => {
    setSubmitting(true);
    setError("");
    try {
      const response = await providerAdminApi.dispatchPolicySync(paymentReference);
      setDispatchMessage(`Dispatch recorded for ${response.main_transaction_reference}.`);
      setPaymentReference("");
      await loadRetries();
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleProcessRetries = async () => {
    setSubmitting(true);
    setError("");
    try {
      const response = await providerAdminApi.processDueRetries();
      setProcessingSummary(response);
      await loadRetries();
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Provider Sync</p>
          <h2>Synchronization center</h2>
        </div>
        <Button onClick={() => void loadRetries()} variant="ghost">
          Refresh
        </Button>
      </section>

      {error ? <ErrorCard message={error} onRetry={() => void loadRetries()} /> : null}

      <section className="if-grid-two">
        <article className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Manual Dispatch</p>
              <h3>Dispatch policy-issued sync</h3>
            </div>
          </div>
          <div className="if-form-stack">
            <TextInput
              label="Payment Reference"
              mono
              placeholder="PAY-20260617-ABC123"
              value={paymentReference}
              onChange={(event) => setPaymentReference(event.target.value)}
            />
            <Button loading={submitting} onClick={() => void handleDispatch()}>
              Dispatch Sync
            </Button>
            {dispatchMessage ? <p className="if-inline-subtitle">{dispatchMessage}</p> : null}
          </div>
        </article>

        <article className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Retry Processing</p>
              <h3>Process due retries</h3>
            </div>
          </div>
          <div className="if-form-stack">
            <Button loading={submitting} onClick={() => void handleProcessRetries()}>
              Process Due Retries
            </Button>
            {processingSummary ? (
              <div className="if-inline-subtitle">
                Processed {processingSummary.processed_count}, succeeded {processingSummary.success_count}, failed {processingSummary.failed_count}.
              </div>
            ) : null}
          </div>
        </article>
      </section>

      <section className="if-surface-card">
        <div className="if-section-heading">
          <div>
            <p className="if-eyebrow">Retry Records</p>
            <h3>Tracked synchronization attempts</h3>
          </div>
        </div>
        {loading ? (
          <div className="if-skeleton-stack">
            <Skeleton height={56} />
            <Skeleton height={56} />
            <Skeleton height={56} />
          </div>
        ) : records.length === 0 ? (
          <p className="if-inline-subtitle">No synchronization retry records have been created yet.</p>
        ) : (
          <div className="if-table-wrap">
            <table className="if-data-table">
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Main Transaction</th>
                  <th>Status</th>
                  <th>Retries</th>
                  <th>Next Retry</th>
                  <th>Last Error</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={`${record.event_type}-${record.main_transaction_reference}-${record.updated_at}`}>
                    <td>{record.event_type}</td>
                    <td className="if-mono">{record.main_transaction_reference}</td>
                    <td>
                      <StatusBadge
                        status={
                          record.status === "SUCCESS"
                            ? "issued"
                            : record.status === "FAILED"
                            ? "failed"
                            : "processing"
                        }
                      >
                        {record.status}
                      </StatusBadge>
                    </td>
                    <td>{record.retry_count}</td>
                    <td>{record.next_retry_at ? new Date(record.next_retry_at).toLocaleString("en-IN") : "Not scheduled"}</td>
                    <td>{record.last_error || "No error"}</td>
                    <td>{new Date(record.updated_at).toLocaleString("en-IN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
