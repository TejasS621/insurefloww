import { CheckCircle2, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { ToggleSwitch } from "../../components/ui/ToggleSwitch";
import type { ApplicationQuote } from "../../services/api/customer";
import { formatCurrencyINR } from "../../utils/formatters";

interface QuoteComparisonScreenProps {
  quotes: ApplicationQuote[];
  transactionReference: string | null;
  loading: boolean;
  error?: string;
  onBack: () => void;
  onRetry?: () => void;
  onProceed: (quoteId: string, selectedAddons: string[]) => Promise<void>;
  isProceeding: boolean;
}

/**
 * QuoteComparisonScreen renders API-backed quote selection with optimistic selection state.
 * Add-on choices are included when the customer confirms the selected plan.
 */
export function QuoteComparisonScreen({
  quotes,
  transactionReference,
  loading,
  error,
  onBack,
  onRetry,
  onProceed,
  isProceeding,
}: QuoteComparisonScreenProps) {
  const [selectedQuoteId, setSelectedQuoteId] = useState<string>("");
  const [enabledAddons, setEnabledAddons] = useState<string[]>([]);

  useEffect(() => {
    if (!selectedQuoteId && quotes.length > 0) {
      setSelectedQuoteId(quotes[0].quote_id);
    }
  }, [quotes, selectedQuoteId]);

  const selectedQuote = quotes.find((quote) => quote.quote_id === selectedQuoteId) ?? quotes[0];
  const selectedAddonObjects =
    selectedQuote?.available_addons.filter((addon) => enabledAddons.includes(addon.addon_code)) ?? [];
  const addonTotal = selectedAddonObjects.reduce((total, addon) => total + addon.addon_price, 0);
  const grandTotal = useMemo(
    () => (selectedQuote?.total_premium ?? 0) + addonTotal,
    [addonTotal, selectedQuote?.total_premium],
  );

  if (loading) {
    return (
      <div className="if-screen-stack">
        <div className="if-grid if-grid-stats">
          <div className="if-skeleton" style={{ height: 320 }} />
          <div className="if-skeleton" style={{ height: 320 }} />
          <div className="if-skeleton" style={{ height: 320 }} />
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorCard message={error} onRetry={onRetry} />;
  }

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <h2>Here are your personalised plans</h2>
          <p className="if-inline-subtitle">
            Compare the strongest matches for your application before choosing one.
          </p>
        </div>
        <span className="if-summary-pill">Transaction | {transactionReference ?? "Pending ref"}</span>
      </section>

      <section className="if-quote-grid">
        {quotes.map((quote, index) => (
          <article
            className={`if-quote-card ${index === 0 ? "is-recommended" : ""} ${
              selectedQuoteId === quote.quote_id ? "is-selected" : ""
            }`}
            key={quote.quote_id}
          >
            {index === 0 ? (
              <div className="if-recommended-badge">
                <Sparkles size={14} />
                Best Value
              </div>
            ) : null}
            <div className="if-quote-provider">
              <div className="if-provider-avatar">
                {quote.provider_name
                  .split(" ")
                  .map((chunk) => chunk[0])
                  .join("")
                  .slice(0, 2)}
              </div>
              <div>
                <p className="if-quote-provider-name">{quote.provider_name}</p>
                <h3>{quote.plan_name}</h3>
              </div>
            </div>
            <p className="if-quote-coverage">{formatCurrencyINR(quote.coverage_amount)}</p>
            <p className="if-quote-monthly">{formatCurrencyINR(quote.total_premium / 12)} / month</p>
            <p className="if-quote-annual">{formatCurrencyINR(quote.total_premium)} billed annually</p>
            <ul className="if-benefit-list">
              {[
                `${quote.provider_name} managed servicing`,
                `Plan code ${quote.plan_code}`,
                "Digital policy issuance",
                "Add-on customisation support",
              ].map((benefit) => (
                <li key={benefit}>
                  <CheckCircle2 size={16} />
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
            <Button className="if-button-full" onClick={() => setSelectedQuoteId(quote.quote_id)}>
              Select Plan
            </Button>
          </article>
        ))}
      </section>

      {selectedQuote ? (
        <section className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Add-ons</p>
              <h2>Enhance your plan</h2>
            </div>
            <StatusBadge status="processing">Customisable</StatusBadge>
          </div>
          <div className="if-addon-stack">
            {selectedQuote.available_addons.map((addon) => {
              const checked = enabledAddons.includes(addon.addon_code);
              return (
                <div className="if-addon-row" key={addon.addon_code}>
                  <div>
                    <h3>{addon.addon_name}</h3>
                    <p>{addon.addon_code}</p>
                  </div>
                  <div className="if-addon-action">
                    <span className="if-addon-price">+{formatCurrencyINR(addon.addon_price)} / year</span>
                    <ToggleSwitch
                      ariaLabel={`Toggle ${addon.addon_name}`}
                      checked={checked}
                      onChange={(nextChecked) =>
                        setEnabledAddons((current) =>
                          nextChecked
                            ? [...current, addon.addon_code]
                            : current.filter((item) => item !== addon.addon_code),
                        )
                      }
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      <div className="if-sticky-total-bar">
        <div>
          <p className="if-total-label">
            Base premium {formatCurrencyINR(selectedQuote?.total_premium ?? 0)} + Add-ons {formatCurrencyINR(addonTotal)} =
          </p>
          <p className="if-total-value">Total {formatCurrencyINR(grandTotal)}</p>
        </div>
        <div className="if-sticky-total-actions">
          <Button onClick={onBack} variant="ghost">
            Back
          </Button>
          <Button
            loading={isProceeding}
            onClick={() => {
              if (!selectedQuoteId) {
                return;
              }
              void onProceed(selectedQuoteId, enabledAddons);
            }}
          >
            Proceed
          </Button>
        </div>
      </div>
    </div>
  );
}
