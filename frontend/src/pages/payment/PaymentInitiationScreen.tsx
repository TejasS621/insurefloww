import { Building2, Headset, Shield } from "lucide-react";

import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { StatusBadge } from "../../components/ui/StatusBadge";
import type { PaymentSession } from "../../services/api/customer";
import { formatCurrencyINR } from "../../utils/formatters";

interface PaymentInitiationScreenProps {
  paymentSession: PaymentSession | null;
  paymentStatus: "idle" | "initiating" | "verifying" | "failed" | "success";
  error?: string;
  onProceed: () => Promise<void>;
  onRetry: () => Promise<void>;
}

/**
 * PaymentInitiationScreen starts hosted checkout and reflects verification polling state.
 * It uses the API payment session response instead of directly contacting the provider.
 */
export function PaymentInitiationScreen({
  paymentSession,
  paymentStatus,
  error,
  onProceed,
  onRetry,
}: PaymentInitiationScreenProps) {
  return (
    <div className="if-screen-stack">
      {error ? <ErrorCard message={error} onRetry={() => void onRetry()} /> : null}

      <section className="if-payment-grid">
        <article className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <StatusBadge status="processing">Hosted Checkout</StatusBadge>
              <h2>Proceed with secure payment</h2>
              <p className="if-inline-subtitle">
                {paymentSession?.payment_reference ?? "Payment session will appear after initiation."}
              </p>
            </div>
          </div>
          <div className="if-payment-lines">
            <div className="if-payment-line">
              <span>Base Premium</span>
              <strong>{formatCurrencyINR(paymentSession?.amount ?? 0)}</strong>
            </div>
            <div className="if-payment-line">
              <span>Gateway</span>
              <strong>{paymentSession?.gateway ?? "Provider Hosted Checkout"}</strong>
            </div>
            <div className="if-payment-line">
              <span>Methods</span>
              <strong>{paymentSession?.available_payment_methods.join(", ") || "UPI, CARD, NETBANKING"}</strong>
            </div>
          </div>
          <div className="if-payment-total">
            <span>Total payable</span>
            <strong>{formatCurrencyINR(paymentSession?.amount ?? 0)}</strong>
          </div>
          <Button
            className="if-button-full"
            loading={paymentStatus === "initiating" || paymentStatus === "verifying"}
            onClick={() => void onProceed()}
          >
            {paymentStatus === "verifying" ? "Verifying payment..." : "Proceed to Pay"}
          </Button>
          <p className="if-payment-note">
            You will be redirected to the secure checkout experience. Payment status is verified with
            polling after initiation.
          </p>
          {paymentStatus === "failed" ? (
            <div className="if-inline-note">
              Payment failed. You can retry the initiation flow from this screen.
            </div>
          ) : null}
        </article>

        <aside className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Trust Signals</p>
              <h2>Secure payment assurance</h2>
            </div>
          </div>
          <div className="if-trust-stack">
            <div className="if-trust-row">
              <Shield size={20} />
              <span>256-bit SSL encrypted</span>
            </div>
            <div className="if-trust-row">
              <Building2 size={20} />
              <span>IRDAI compliant</span>
            </div>
            <div className="if-trust-row">
              <Headset size={20} />
              <span>24x7 customer support</span>
            </div>
          </div>
          <div className="if-logo-block">
            {(paymentSession?.available_payment_methods ?? ["UPI", "CARD", "NETBANKING"]).map((method) => (
              <span className="if-logo-pill" key={method}>
                {method}
              </span>
            ))}
          </div>
        </aside>
      </section>
    </div>
  );
}
