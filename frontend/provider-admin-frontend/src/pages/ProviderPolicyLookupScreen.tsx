import { useState } from "react";

import { Button } from "../components/ui/Button";
import { ErrorCard } from "../components/ui/ErrorCard";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TextInput } from "../components/ui/TextInput";
import {
  providerAdminApi,
  type ProviderPolicyResponse,
} from "../services/api/providerAdmin";
import { normalizeApiError } from "../utils/apiErrors";

export function ProviderPolicyLookupScreen() {
  const [policyNumber, setPolicyNumber] = useState("");
  const [policy, setPolicy] = useState<ProviderPolicyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLookup = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await providerAdminApi.getPolicy(policyNumber);
      setPolicy(response);
    } catch (requestError) {
      setPolicy(null);
      setError(normalizeApiError(requestError).message);
    } finally {
      setLoading(false);
    }
  };

  const openBlobInNewTab = (blob: Blob) => {
    const objectUrl = URL.createObjectURL(blob);
    window.open(objectUrl, "_blank", "noopener,noreferrer");
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filename;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
  };

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Provider Policies</p>
          <h2>Lookup issued policy</h2>
        </div>
      </section>

      {error ? <ErrorCard message={error} onRetry={() => void handleLookup()} /> : null}

      <section className="if-surface-card">
        <div className="if-form-inline">
          <TextInput
            label="Policy Number"
            mono
            onChange={(event) => setPolicyNumber(event.target.value)}
            placeholder="POL-20260617-ABCD1234"
            value={policyNumber}
          />
          <Button loading={loading} onClick={() => void handleLookup()}>
            Fetch Policy
          </Button>
        </div>
      </section>

      {policy ? (
        <section className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Policy Details</p>
              <h3 className="if-mono">{policy.policy_number}</h3>
            </div>
            <StatusBadge
              status={policy.policy_status === "ISSUED" ? "issued" : "processing"}
            >
              {policy.policy_status}
            </StatusBadge>
          </div>

          <div className="if-detail-grid">
            <div>
              <span className="if-detail-label">Main Transaction</span>
              <span className="if-detail-value if-mono">
                {policy.main_transaction_reference}
              </span>
            </div>
            <div>
              <span className="if-detail-label">Provider Transaction</span>
              <span className="if-detail-value if-mono">
                {policy.provider_transaction_reference}
              </span>
            </div>
            <div>
              <span className="if-detail-label">Coverage Amount</span>
              <span className="if-detail-value">
                INR {policy.coverage_amount.toLocaleString("en-IN")}
              </span>
            </div>
            <div>
              <span className="if-detail-label">Premium Amount</span>
              <span className="if-detail-value">
                INR {policy.premium_amount.toLocaleString("en-IN")}
              </span>
            </div>
            <div>
              <span className="if-detail-label">Issue Date</span>
              <span className="if-detail-value">{policy.issue_date || "N/A"}</span>
            </div>
            <div>
              <span className="if-detail-label">End Date</span>
              <span className="if-detail-value">{policy.end_date || "N/A"}</span>
            </div>
          </div>

          <div className="if-form-inline">
            <Button
              onClick={() => {
                void providerAdminApi
                  .getPolicyDocument(policy.policy_number)
                  .then((blob) => {
                    openBlobInNewTab(blob);
                  })
                  .catch((requestError) => {
                    setError(normalizeApiError(requestError).message);
                  });
              }}
              variant="ghost"
            >
              View Document
            </Button>
            <Button
              onClick={() => {
                void providerAdminApi
                  .downloadPolicyDocument(policy.policy_number)
                  .then((blob) => {
                    downloadBlob(blob, `${policy.policy_number}.pdf`);
                  })
                  .catch((requestError) => {
                    setError(normalizeApiError(requestError).message);
                  });
              }}
            >
              Download Policy
            </Button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
