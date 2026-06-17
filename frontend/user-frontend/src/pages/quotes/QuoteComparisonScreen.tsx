import { CheckCircle2, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
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

  const summaryText = useMemo(() => {
    if (!quotes || quotes.length === 0) return "";
    const firstQuote = quotes[0];
    const isHealth = firstQuote.plan_code.includes("HL") || firstQuote.plan_code.includes("HEALTH");
    const isLife = firstQuote.plan_code.includes("LF") || firstQuote.plan_code.includes("LIFE");
    const isVehicle = firstQuote.plan_code.includes("VH") || firstQuote.plan_code.includes("VEHICLE");
    
    let typeLabel = "Insurance";
    if (isHealth) typeLabel = "Health";
    else if (isLife) typeLabel = "Life";
    else if (isVehicle) typeLabel = "Vehicle";

    const coverageLakhs = firstQuote.coverage_amount / 100000;
    const coverageLabel = coverageLakhs >= 100 ? `₹${coverageLakhs / 100}Cr` : `₹${coverageLakhs}L`;
    return `${typeLabel} · ${coverageLabel} coverage · 1 year`;
  }, [quotes]);

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
      <section className="if-section-heading" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h2 style={{ color: "var(--if-text-1)", fontSize: "24px", fontWeight: 600, margin: 0 }}>Your personalised plans</h2>
          <p className="if-inline-subtitle" style={{ color: "var(--if-text-2)", margin: "4px 0 0" }}>
            Compare the strongest matches for your application before choosing one.
          </p>
        </div>
        <span
          className="if-summary-pill"
          style={{
            background: "rgba(124, 58, 237, 0.15)",
            border: "1px solid var(--if-violet)",
            borderRadius: "var(--radius-pill)",
            color: "var(--if-text-1)",
            padding: "8px 16px",
            fontSize: "13px",
            fontWeight: 500
          }}
        >
          {summaryText || `Reference | ${transactionReference ?? "Pending"}`}
        </span>
      </section>

      <section className="if-quote-grid">
        {quotes.map((quote, index) => {
          const isRecommended = index === 0;
          const isSelected = selectedQuoteId === quote.quote_id || quote.quote_status === "SELECTED";
          return (
            <article
              className={`if-quote-card ${isRecommended ? "is-recommended" : ""} ${
                isSelected ? "is-selected" : ""
              }`}
              key={quote.quote_id}
              style={{
                background: "var(--if-card-bg)",
                border: isRecommended ? "2px solid var(--if-violet)" : "1px solid var(--if-border)",
                backgroundColor: isRecommended ? "rgba(124, 58, 237, 0.06)" : "var(--if-card-bg)",
                borderRadius: "var(--radius-md)",
                padding: "28px 24px",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
                position: "relative"
              }}
            >
              {isRecommended ? (
                <div
                  className="if-recommended-badge"
                  style={{
                    background: "var(--if-grad-primary)",
                    color: "var(--if-text-inverse)",
                    fontSize: "11px",
                    fontWeight: 600,
                    padding: "3px 10px",
                    borderRadius: "var(--radius-pill)",
                    position: "absolute",
                    right: "18px",
                    top: "18px"
                  }}
                >
                  <Sparkles size={11} style={{ display: "inline", marginRight: "4px" }} />
                  Best Value
                </div>
              ) : null}

              <div className="if-quote-provider" style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                <div
                  className="if-provider-avatar"
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "50%",
                    background: "var(--if-violet)",
                    color: "var(--if-text-inverse)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "14px"
                  }}
                >
                  {quote.provider_name
                    .split(" ")
                    .map((chunk) => chunk[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()}
                </div>
                <div>
                  <p className="if-quote-provider-name" style={{ color: "var(--if-text-2)", margin: 0, fontSize: "13px" }}>
                    {quote.provider_name}
                  </p>
                  <h3 style={{ color: "var(--if-text-1)", margin: 0, fontSize: "17px", fontWeight: 600 }}>{quote.plan_name}</h3>
                </div>
              </div>

              <div style={{ marginTop: "8px" }}>
                <p className="if-quote-coverage" style={{ color: "var(--if-cyan)", fontSize: "22px", fontWeight: 700, margin: 0 }}>
                  {formatCurrencyINR(quote.coverage_amount)}
                </p>
                <p className="if-quote-monthly" style={{ color: "var(--if-text-1)", fontSize: "32px", fontWeight: 700, margin: "4px 0 0" }}>
                  {formatCurrencyINR(Math.round(quote.total_premium / 12))} <span style={{ fontSize: "16px", fontWeight: 400, color: "var(--if-text-2)" }}>/ mo</span>
                </p>
                <p className="if-quote-annual" style={{ color: "var(--if-text-2)", fontSize: "14px", margin: "2px 0 0" }}>
                  {formatCurrencyINR(quote.total_premium)} / yr
                </p>
              </div>

              <hr style={{ borderColor: "var(--if-border)", margin: "8px 0 4px", borderStyle: "solid", borderWidth: "0.5px" }} />

              <ul className="if-benefit-list" style={{ display: "grid", gap: "10px", padding: 0, listStyle: "none", margin: 0 }}>
                {[
                  `${quote.provider_name} managed servicing`,
                  `Plan code: ${quote.plan_code}`,
                  "Digital policy issuance",
                  "Add-on customisation support",
                ].map((benefit) => (
                  <li key={benefit} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "14px", color: "var(--if-text-1)" }}>
                    <CheckCircle2 size={15} style={{ color: "var(--if-cyan)", flexShrink: 0 }} />
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>

              <Button
                variant={isSelected ? "primary" : "ghost"}
                className="if-button-full"
                onClick={() => setSelectedQuoteId(quote.quote_id)}
                style={{ marginTop: "auto" }}
              >
                Select Plan
              </Button>
            </article>
          );
        })}
      </section>

      {selectedQuote ? (
        <section className="if-surface-card" style={{ marginTop: "32px", background: "var(--if-card-bg)" }}>
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Enhance your plan</p>
              <h2 style={{ color: "var(--if-text-1)", fontSize: "18px", fontWeight: 600 }}>Optional Add-ons</h2>
            </div>
          </div>
          <div className="if-addon-stack" style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
            {selectedQuote.available_addons.map((addon) => {
              const checked = enabledAddons.includes(addon.addon_code);
              return (
                <div
                  className="if-addon-row"
                  key={addon.addon_code}
                  style={{
                    background: "var(--if-card-bg)",
                    borderRadius: "var(--radius-sm)",
                    padding: "14px 16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    border: "1px solid var(--if-border)"
                  }}
                >
                  <div>
                    <h3 style={{ color: "var(--if-text-1)", fontSize: "15px", fontWeight: 600, margin: 0 }}>{addon.addon_name}</h3>
                    <p style={{ color: "var(--if-text-2)", fontSize: "13px", margin: "2px 0 0" }}>{addon.addon_code}</p>
                  </div>
                  <div className="if-addon-action" style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                    <span className="if-addon-price" style={{ color: "var(--if-cyan)", fontSize: "14px", fontWeight: 500 }}>
                      +{formatCurrencyINR(addon.addon_price)} / yr
                    </span>
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

      <div
        className="if-sticky-total-bar"
        style={{
          background: "color-mix(in srgb, var(--if-charcoal) 92%, transparent)",
          backdropFilter: "blur(12px)",
          border: "1px solid var(--if-border)",
          borderRadius: "var(--radius-md)",
          padding: "18px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          position: "sticky",
          bottom: "16px",
          zIndex: 30,
          marginTop: "32px",
          boxShadow: "var(--shadow-card)"
        }}
      >
        <div>
          <p className="if-total-label" style={{ color: "var(--if-text-2)", margin: 0, fontSize: "13px" }}>
            Base {formatCurrencyINR(selectedQuote?.total_premium ?? 0)} + Add-ons {formatCurrencyINR(addonTotal)} =
          </p>
          <p className="if-total-value" style={{ color: "var(--if-text-inverse)", fontSize: "20px", fontWeight: 700, margin: "4px 0 0" }}>
            Total {formatCurrencyINR(grandTotal)}
          </p>
        </div>
        <div className="if-sticky-total-actions" style={{ display: "flex", gap: "12px" }}>
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
