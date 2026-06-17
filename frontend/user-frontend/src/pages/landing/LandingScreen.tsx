import { useState, useMemo } from "react";
import type { LucideIcon } from "lucide-react";
import {
  CarFront,
  HeartPulse,
  Home,
  Luggage,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";

import { Button } from "../../components/ui/Button";

type InsuranceType = "health" | "vehicle" | "travel" | "home" | "life";

interface LandingScreenProps {
  onSelectType: (type: InsuranceType) => void;
  onLogin: () => void;
}

interface InsuranceCardItem {
  type: InsuranceType;
  title: string;
  description: string;
  icon: LucideIcon;
}

const insuranceCards: InsuranceCardItem[] = [
  {
    type: "health",
    title: "Health",
    description: "Protect your family with flexible health and wellness coverage.",
    icon: HeartPulse,
  },
  {
    type: "vehicle",
    title: "Vehicle",
    description: "Secure your car or bike with repair, theft, and third-party cover.",
    icon: CarFront,
  },
  {
    type: "travel",
    title: "Travel",
    description: "Stay covered for delays, medical issues, and baggage loss abroad.",
    icon: Luggage,
  },
  {
    type: "home",
    title: "Home",
    description: "Protect your home and essentials from fire, damage, and loss.",
    icon: Home,
  },
  {
    type: "life",
    title: "Life",
    description: "Build long-term security with dependable life protection plans.",
    icon: ShieldCheck,
  },
];

/**
 * LandingScreen introduces the customer journey and insurance-type selection.
 * It uses the shared hero, button, and card language from the design system.
 */
export function LandingScreen({ onSelectType, onLogin }: LandingScreenProps) {
  const [selectedCard, setSelectedCard] = useState<InsuranceType>("health");

  return (
    <div className="if-screen-stack">
      <section className="if-customer-hero">
        <div className="if-customer-hero-copy">
          <p
            className="if-eyebrow"
            style={{
              color: "var(--if-cyan)",
              fontSize: "13px",
              fontWeight: 500,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              marginBottom: "16px",
            }}
          >
            Trusted by 1,00,000+ Indians
          </p>
          <h1
            className="if-customer-hero-title"
            style={{
              fontSize: "36px",
              fontWeight: 700,
              lineHeight: 1.2,
              color: "var(--if-text-inverse)",
              marginBottom: "16px",
            }}
          >
            Insure what matters. In minutes.
          </h1>
          <p
            className="if-customer-hero-text"
            style={{
              color: "var(--if-text-inverse-muted)",
              fontSize: "18px",
              lineHeight: 1.6,
              maxWidth: "600px",
              margin: "0 auto 32px",
            }}
          >
            Compare plans, choose coverage, get your policy — all in one place.
          </p>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "16px",
            }}
          >
            <Button
              onClick={() => onSelectType(selectedCard)}
              size="large"
              style={{ padding: "12px 36px" }}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                Get Started <ArrowRight size={16} />
              </span>
            </Button>
            <Button
              onClick={onLogin}
              variant="ghost"
              style={{
                color: "var(--if-text-2)",
                fontSize: "14px",
              }}
            >
              Customer Login
            </Button>
          </div>
        </div>
      </section>

      <section className="if-screen-section">
        <div className="if-section-heading">
          <div>
            <p className="if-eyebrow">Insurance Type</p>
            <h2>Choose your coverage journey</h2>
          </div>
        </div>
        <div className="if-insurance-grid">
          {insuranceCards.map((card) => {
            const Icon = card.icon;
            const isSelected = selectedCard === card.type;
            return (
              <article
                className={`if-insurance-card ${isSelected ? "is-selected" : ""}`}
                key={card.type}
                onClick={() => setSelectedCard(card.type)}
                style={{ cursor: "pointer" }}
              >
                <div className="if-insurance-icon" style={{ color: "var(--if-violet)" }}>
                  <Icon size={48} strokeWidth={1.8} />
                </div>
                <h3 style={{ color: "var(--if-text-1)", fontSize: "17px", fontWeight: 600, margin: 0 }}>
                  {card.title}
                </h3>
                <p style={{ color: "var(--if-text-2)", fontSize: "14px", margin: 0, minHeight: "44px" }}>
                  {card.description}
                </p>
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectType(card.type);
                  }}
                  variant={isSelected ? "primary" : "ghost"}
                  style={{ width: "100%", marginTop: "auto" }}
                >
                  Explore Plans
                </Button>
              </article>
            );
          })}
        </div>
      </section>
    </div>
  );
}
