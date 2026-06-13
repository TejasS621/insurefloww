import { CheckCircle2, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { ToggleSwitch } from "../../components/ui/ToggleSwitch";
import { formatCurrencyINR } from "../../utils/formatters";

interface QuoteComparisonScreenProps {
  onBack: () => void;
  onProceed: () => void;
}

const quoteCards = [
  {
    id: "care-plus",
    provider: "Care Secure",
    initials: "CS",
    planName: "Care Plus Shield",
    coverageAmount: 1000000,
    monthlyPremium: 1890,
    annualPremium: 22680,
    benefits: [
      "Cashless network hospitals",
      "Day-care treatment cover",
      "No-claim bonus booster",
      "Free annual health check",
    ],
  },
  {
    id: "nova-prime",
    provider: "Nova Life",
    initials: "NL",
    planName: "Nova Prime Protect",
    coverageAmount: 1000000,
    monthlyPremium: 1725,
    annualPremium: 20700,
    benefits: [
      "OPD consultation add-on ready",
      "Room rent flexibility",
      "Fast digital claim support",
      "Wellness rewards tracking",
    ],
    recommended: true,
  },
  {
    id: "aegis-elite",
    provider: "Aegis Health",
    initials: "AH",
    planName: "Aegis Elite Cover",
    coverageAmount: 1000000,
    monthlyPremium: 2140,
    annualPremium: 25680,
    benefits: [
      "Maternity waiting reduction",
      "Global second opinion access",
      "Restoration of sum insured",
      "Preventive health package",
    ],
  },
];

const addonCatalog = [
  {
    id: "wellness",
    name: "Wellness Booster",
    description: "Extra preventive checkups and nutrition consultations.",
    amount: 2400,
  },
  {
    id: "maternity",
    name: "Maternity Support",
    description: "Expanded maternity and newborn benefit support.",
    amount: 5200,
  },
  {
    id: "global",
    name: "Global Emergency Rider",
    description: "Emergency stabilization support while travelling abroad.",
    amount: 3600,
  },
];

/**
 * QuoteComparisonScreen presents plan cards, add-ons, and the running premium total.
 * It gives customers a focused compare and proceed step before payment initiation.
 */
export function QuoteComparisonScreen({ onBack, onProceed }: QuoteComparisonScreenProps) {
  const [selectedQuoteId, setSelectedQuoteId] = useState("nova-prime");
  const [enabledAddons, setEnabledAddons] = useState<string[]>(["wellness"]);

  const selectedQuote = quoteCards.find((quote) => quote.id === selectedQuoteId) ?? quoteCards[1];
  const addonTotal = enabledAddons.reduce((total, addonId) => {
    const addon = addonCatalog.find((item) => item.id === addonId);
    return total + (addon?.amount ?? 0);
  }, 0);
  const grandTotal = useMemo(
    () => selectedQuote.annualPremium + addonTotal,
    [addonTotal, selectedQuote.annualPremium],
  );

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <h2>Here are your personalised plans</h2>
          <p className="if-inline-subtitle">
            Compare the strongest matches for your application before choosing one.
          </p>
        </div>
        <span className="if-summary-pill">Health | ₹10L Coverage</span>
      </section>

      <section className="if-quote-grid">
        {quoteCards.map((quote) => (
          <article
            className={`if-quote-card ${quote.recommended ? "is-recommended" : ""} ${
              selectedQuoteId === quote.id ? "is-selected" : ""
            }`}
            key={quote.id}
          >
            {quote.recommended ? (
              <div className="if-recommended-badge">
                <Sparkles size={14} />
                Best Value
              </div>
            ) : null}
            <div className="if-quote-provider">
              <div className="if-provider-avatar">{quote.initials}</div>
              <div>
                <p className="if-quote-provider-name">{quote.provider}</p>
                <h3>{quote.planName}</h3>
              </div>
            </div>
            <p className="if-quote-coverage">{formatCurrencyINR(quote.coverageAmount)}</p>
            <p className="if-quote-monthly">{formatCurrencyINR(quote.monthlyPremium)} / month</p>
            <p className="if-quote-annual">{formatCurrencyINR(quote.annualPremium)} billed annually</p>
            <ul className="if-benefit-list">
              {quote.benefits.map((benefit) => (
                <li key={benefit}>
                  <CheckCircle2 size={16} />
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
            <Button className="if-button-full" onClick={() => setSelectedQuoteId(quote.id)}>
              Select Plan
            </Button>
          </article>
        ))}
      </section>

      <section className="if-surface-card">
        <div className="if-section-heading">
          <div>
            <p className="if-eyebrow">Add-ons</p>
            <h2>Enhance your plan</h2>
          </div>
          <StatusBadge status="processing">Customisable</StatusBadge>
        </div>
        <div className="if-addon-stack">
          {addonCatalog.map((addon) => {
            const checked = enabledAddons.includes(addon.id);
            return (
              <div className="if-addon-row" key={addon.id}>
                <div>
                  <h3>{addon.name}</h3>
                  <p>{addon.description}</p>
                </div>
                <div className="if-addon-action">
                  <span className="if-addon-price">+{formatCurrencyINR(addon.amount)} / year</span>
                  <ToggleSwitch
                    ariaLabel={`Toggle ${addon.name}`}
                    checked={checked}
                    onChange={(nextChecked) =>
                      setEnabledAddons((current) =>
                        nextChecked
                          ? [...current, addon.id]
                          : current.filter((item) => item !== addon.id),
                      )
                    }
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <div className="if-sticky-total-bar">
        <div>
          <p className="if-total-label">
            Base premium {formatCurrencyINR(selectedQuote.annualPremium)} + Add-ons {formatCurrencyINR(addonTotal)} =
          </p>
          <p className="if-total-value">Total {formatCurrencyINR(grandTotal)}</p>
        </div>
        <div className="if-sticky-total-actions">
          <Button onClick={onBack} variant="ghost">
            Back
          </Button>
          <Button onClick={onProceed}>Proceed</Button>
        </div>
      </div>
    </div>
  );
}
