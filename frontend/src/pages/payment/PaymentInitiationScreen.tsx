import { Shield, Award, Headset, Lock } from "lucide-react";

import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { StatusBadge } from "../../components/ui/StatusBadge";
import type { PaymentSession } from "../../services/api/customer";
import { formatCurrencyINR } from "../../utils/formatters";

interface PaymentBreakdown {
  insuranceType: string;
  providerName: string;
  planName: string;
  basePremium: number;
  taxAmount: number;
  addonAmount: number;
  totalAmount: number;
  selectedAddons: Array<{
    addon_code: string;
    addon_name: string;
    addon_price: number;
  }>;
}

interface PaymentInitiationScreenProps {
  paymentSession: PaymentSession | null;
  paymentBreakdown: PaymentBreakdown | null;
  paymentStatus: "idle" | "initiating" | "verifying" | "failed" | "success";
  isAuthenticated: boolean;
  error?: string;
  onBackHome: () => void;
  onLoginToTrack: () => void;
  onOpenDashboard: () => void;
  onProceed: () => Promise<void>;
  onRetry: () => Promise<void>;
}

export function PaymentInitiationScreen({
  paymentSession,
  paymentBreakdown,
  paymentStatus,
  isAuthenticated,
  error,
  onBackHome,
  onLoginToTrack,
  onOpenDashboard,
  onProceed,
  onRetry,
}: PaymentInitiationScreenProps) {
  const totalPayable = paymentSession?.amount ?? paymentBreakdown?.totalAmount ?? 0;
  const gst = paymentBreakdown?.taxAmount ?? 0;
  const addons = paymentBreakdown?.addonAmount ?? 0;
  const base = paymentBreakdown?.basePremium ?? Math.max(totalPayable - addons - gst, 0);
  const insuranceType = paymentBreakdown?.insuranceType ?? "INSURANCE";
  const planName = paymentBreakdown?.planName ?? "Selected Plan";
  const providerName = paymentBreakdown?.providerName ?? "Provider";

  return (
    <div className="if-screen-stack">
      {error ? <ErrorCard message={error} onRetry={() => void onRetry()} /> : null}

      <section className="if-payment-grid">
        {/* Left Column: Order Summary */}
        <article
          className="if-surface-card"
          style={{
            background: "var(--if-card-bg)",
            border: "1px solid var(--if-border)",
            borderRadius: "var(--radius-md)",
            padding: "28px 24px",
            display: "flex",
            flexDirection: "column",
            gap: "20px"
          }}
        >
          <div className="if-section-heading" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%", margin: 0 }}>
            <div>
              <span className="if-badge if-badge-admin" style={{ marginBottom: "8px" }}>
                {insuranceType}
              </span>
              <h2 style={{ color: "var(--if-text-1)", fontSize: "20px", fontWeight: 600, margin: 0 }}>
                {planName}
              </h2>
              <p className="if-inline-subtitle" style={{ color: "var(--if-text-2)", fontSize: "14px", margin: "4px 0 0" }}>
                {providerName} · {paymentSession?.payment_reference ?? "Pending checkout reference"}
              </p>
            </div>
          </div>

          <div className="if-payment-lines" style={{ display: "grid", gap: "14px", marginTop: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "15px", color: "var(--if-text-2)" }}>
              <span>Base Premium</span>
              <strong style={{ color: "var(--if-text-1)", font: "var(--fs-mono)" }}>{formatCurrencyINR(base)}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "15px", color: "var(--if-text-2)" }}>
              <span>Add-ons</span>
              <strong style={{ color: "var(--if-text-1)", font: "var(--fs-mono)" }}>{formatCurrencyINR(addons)}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "15px", color: "var(--if-text-2)" }}>
              <span>GST (18%)</span>
              <strong style={{ color: "var(--if-text-1)", font: "var(--fs-mono)" }}>{formatCurrencyINR(gst)}</strong>
            </div>
          </div>

          <hr style={{ borderColor: "var(--if-border)", margin: "8px 0 0", borderStyle: "solid", borderWidth: "0.5px" }} />

          <div className="if-payment-total" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0" }}>
            <span style={{ color: "var(--if-text-1)", fontSize: "16px", fontWeight: 500 }}>Total Payable</span>
            <strong style={{ color: "var(--if-text-1)", fontSize: "22px", fontWeight: 700 }}>{formatCurrencyINR(totalPayable)}</strong>
          </div>

          <Button
            className="if-button-full"
            loading={paymentStatus === "initiating" || paymentStatus === "verifying"}
            disabled={paymentStatus === "success"}
            onClick={() => void onProceed()}
            style={{ minHeight: "48px" }}
          >
            {paymentStatus === "verifying"
              ? "Verifying payment..."
              : paymentStatus === "success"
                ? "Payment Completed"
                : "Proceed to Pay"}
          </Button>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", color: "var(--if-text-2)", fontSize: "13px", marginTop: "8px" }}>
            <Lock size={14} style={{ color: "var(--if-success)" }} />
            <span>Secured by Razorpay · 256-bit SSL</span>
          </div>

          {paymentStatus === "failed" ? (
            <div className="if-inline-note" style={{ color: "var(--if-danger)", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)", borderRadius: "var(--radius-md)", padding: "12px 14px", fontSize: "14px" }}>
              Payment failed. You can retry the checkout initiation flow.
            </div>
          ) : null}

          {paymentStatus === "success" ? (
            <div
              className="if-inline-note"
              style={{
                background: "rgba(16,185,129,0.1)",
                border: "1px solid rgba(16,185,129,0.2)",
                borderRadius: "var(--radius-md)",
                color: "var(--if-success)",
                display: "grid",
                gap: "12px",
                padding: "14px 16px",
              }}
            >
              <div>
                Payment completed successfully. You can now track policy issuance and download the
                policy once it is available.
              </div>
              {!isAuthenticated ? (
                <div style={{ color: "var(--if-text-2)", fontSize: "13px" }}>
                  Login with the same mobile number used in the application to view your policy and payment status.
                </div>
              ) : null}
              <div className="if-table-action-row">
                {isAuthenticated ? (
                  <Button onClick={onOpenDashboard}>Open Dashboard</Button>
                ) : (
                  <Button onClick={onLoginToTrack}>Login to Check Status</Button>
                )}
                <Button onClick={onBackHome} variant="ghost">
                  Back to Home
                </Button>
              </div>
            </div>
          ) : null}
        </article>

        {/* Right Column: Trust block */}
        <aside
          className="if-surface-card"
          style={{
            background: "var(--if-card-alt)",
            border: "1px solid var(--if-border)",
            borderRadius: "var(--radius-md)",
            padding: "28px 24px",
            display: "flex",
            flexDirection: "column",
            gap: "24px"
          }}
        >
          <div className="if-section-heading" style={{ margin: 0 }}>
            <div>
              <p className="if-eyebrow">Trust Assurance</p>
              <h2 style={{ color: "var(--if-text-1)", fontSize: "20px", fontWeight: 600 }}>Why InsureFlow?</h2>
            </div>
          </div>

          <div className="if-trust-stack" style={{ display: "grid", gap: "20px" }}>
            <div style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
              <div style={{ color: "var(--if-cyan)", marginTop: "2px" }}>
                <Shield size={22} />
              </div>
              <div>
                <strong style={{ color: "var(--if-text-1)", display: "block", fontSize: "15px", fontWeight: 600 }}>SSL Encrypted</strong>
                <span style={{ color: "var(--if-text-2)", fontSize: "13px" }}>Your data is safe</span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
              <div style={{ color: "var(--if-cyan)", marginTop: "2px" }}>
                <Award size={22} />
              </div>
              <div>
                <strong style={{ color: "var(--if-text-1)", display: "block", fontSize: "15px", fontWeight: 600 }}>IRDAI Compliant</strong>
                <span style={{ color: "var(--if-text-2)", fontSize: "13px" }}>Regulated by IRDAI</span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
              <div style={{ color: "var(--if-cyan)", marginTop: "2px" }}>
                <Headset size={22} />
              </div>
              <div>
                <strong style={{ color: "#fff", display: "block", fontSize: "15px", fontWeight: 600 }}>24×7 Support</strong>
                <span style={{ color: "var(--if-text-2)", fontSize: "13px" }}>Always here for you</span>
              </div>
            </div>
          </div>

          <hr style={{ borderColor: "var(--if-border)", margin: "8px 0 0", borderStyle: "solid", borderWidth: "0.5px" }} />

          <div>
            <p style={{ color: "var(--if-text-2)", fontSize: "13px", marginBottom: "12px", fontWeight: 500 }}>Accepted Payments</p>
            <div className="if-logo-block" style={{ display: "flex", gap: "10px", flexWrap: "wrap", margin: 0 }}>
              {["UPI", "Visa", "Mastercard", "Netbanking"].map((method) => (
                <span
                  className="if-logo-pill"
                  key={method}
                  style={{
                    background: "var(--if-input-bg)",
                    border: "1px solid var(--if-border)",
                    borderRadius: "var(--radius-sm)",
                    color: "var(--if-text-2)",
                    fontSize: "12px",
                    padding: "6px 12px",
                    fontWeight: 500
                  }}
                >
                  {method}
                </span>
              ))}
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
}
