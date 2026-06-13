import { Building2, Headset, Shield } from "lucide-react";

import { Button } from "../../components/ui/Button";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { formatCurrencyINR } from "../../utils/formatters";

interface PaymentInitiationScreenProps {
  onProceed: () => void;
}

/**
 * PaymentInitiationScreen summarizes the selected plan before checkout redirect.
 * It pairs a payment summary with trust markers and payment-method reassurance.
 */
export function PaymentInitiationScreen({ onProceed }: PaymentInitiationScreenProps) {
  return (
    <div className="if-screen-stack">
      <section className="if-payment-grid">
        <article className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <StatusBadge status="processing">Health Insurance</StatusBadge>
              <h2>Nova Prime Protect</h2>
              <p className="if-inline-subtitle">Provider: Nova Life</p>
            </div>
          </div>
          <div className="if-payment-lines">
            <div className="if-payment-line">
              <span>Base Premium</span>
              <strong>{formatCurrencyINR(20700)}</strong>
            </div>
            <div className="if-payment-line">
              <span>Add-ons</span>
              <strong>{formatCurrencyINR(2400)}</strong>
            </div>
            <div className="if-payment-line">
              <span>Taxes</span>
              <strong>{formatCurrencyINR(4158)}</strong>
            </div>
          </div>
          <div className="if-payment-total">
            <span>Total payable</span>
            <strong>{formatCurrencyINR(27258)}</strong>
          </div>
          <Button className="if-button-full" onClick={onProceed}>
            Proceed to Pay
          </Button>
          <p className="if-payment-note">
            You will be redirected to the secure Razorpay checkout.
          </p>
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
            <span className="if-logo-pill">Razorpay</span>
            <span className="if-logo-pill">UPI</span>
            <span className="if-logo-pill">Cards</span>
            <span className="if-logo-pill">Netbanking</span>
          </div>
        </aside>
      </section>
    </div>
  );
}
