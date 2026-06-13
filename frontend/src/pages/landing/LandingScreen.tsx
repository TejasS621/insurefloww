import type { LucideIcon } from "lucide-react";
import {
  CarFront,
  HeartPulse,
  Home,
  Luggage,
  ShieldCheck,
} from "lucide-react";

import { Button } from "../../components/ui/Button";

type InsuranceType = "health" | "vehicle" | "travel" | "home" | "life";

interface LandingScreenProps {
  onSelectType: (type: InsuranceType) => void;
}

interface InsuranceCard {
  type: InsuranceType;
  title: string;
  description: string;
  icon: LucideIcon;
}

const insuranceCards: InsuranceCard[] = [
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
export function LandingScreen({ onSelectType }: LandingScreenProps) {
  return (
    <div className="if-screen-stack">
      <section className="if-customer-hero">
        <div className="if-customer-hero-copy">
          <h1 className="if-customer-hero-title">Insure what matters. In minutes.</h1>
          <p className="if-customer-hero-text">
            Compare plans, choose coverage, get your policy, all in one place.
          </p>
          <Button onClick={() => onSelectType("health")} size="large">
            Get Started
          </Button>
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
            return (
              <article className="if-insurance-card" key={card.type}>
                <div className="if-insurance-icon">
                  <Icon size={64} strokeWidth={1.8} />
                </div>
                <h3>{card.title}</h3>
                <p>{card.description}</p>
                <Button onClick={() => onSelectType(card.type)} variant="ghost">
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
