import { useEffect, useRef } from "react";
import type { LucideIcon } from "lucide-react";
import {
  CarFront,
  HeartPulse,
  Home,
  Luggage,
  ShieldCheck,
  ArrowRight,
  ChevronDown,
  MessageSquareText,
  Mic,
  Sparkles,
  BadgeCheck,
} from "lucide-react";

import { Button } from "../../components/ui/Button";
import { HeroInkRibbon } from "./HeroInkRibbon";

type InsuranceType = "health" | "vehicle" | "travel" | "home" | "life";

interface LandingScreenProps {
  onSelectType: (type: InsuranceType) => void;
  onLogin: () => void;
  onLauncherVisibilityChange?: (visible: boolean) => void;
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
export function LandingScreen({
  onSelectType,
  onLogin,
  onLauncherVisibilityChange,
}: LandingScreenProps) {
  const launcherSectionRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const section = launcherSectionRef.current;
    if (!section || !onLauncherVisibilityChange) {
      return undefined;
    }

    onLauncherVisibilityChange(false);

    const observer = new IntersectionObserver(
      ([entry]) => {
        onLauncherVisibilityChange(entry.isIntersecting);
      },
      {
        threshold: 0.2,
      },
    );

    observer.observe(section);

    return () => {
      observer.disconnect();
      onLauncherVisibilityChange(false);
    };
  }, [onLauncherVisibilityChange]);

  return (
    <div className="if-screen-stack if-landing-stack">
      <section className="if-customer-hero if-customer-hero-with-ribbon if-landing-hero-shell">
        <HeroInkRibbon />
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
              color: "var(--color-text-primary)",
              marginBottom: "16px",
            }}
          >
            Insure what matters. In minutes.
          </h1>
          <p
            className="if-customer-hero-text"
            style={{
              color: "var(--color-text-secondary)",
              fontSize: "18px",
              lineHeight: 1.6,
              maxWidth: "600px",
              margin: "0 auto 32px",
            }}
          >
            Compare plans, choose coverage, get your policy — all in one place.
          </p>
          <div className="if-landing-hero-actions">
            <Button
              onClick={() => onSelectType("health")}
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
        <div className="if-landing-scroll-cue" aria-hidden="true">
          <span>Scroll</span>
          <ChevronDown size={16} />
        </div>
      </section>

      <section className="if-screen-section if-landing-section" ref={launcherSectionRef}>
        <div className="if-landing-section-inner">
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
                <article
                  className="if-insurance-card"
                  key={card.type}
                  onClick={() => onSelectType(card.type)}
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
                    variant="ghost"
                    style={{ width: "100%", marginTop: "auto" }}
                  >
                    Explore Plans
                  </Button>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="if-screen-section if-landing-section if-landing-assistant-section">
        <div className="if-landing-section-inner">
          <div className="if-landing-assistant-shell">
            <div className="if-landing-assistant-copy">
              <p className="if-eyebrow">Talk to InsureFlow</p>
              <h2>Get guidance the way you prefer.</h2>
              <p className="if-landing-assistant-text">
                Ask questions in chat, explore policy options faster, or use voice support
                when you want a more guided insurance journey.
              </p>

              <div className="if-landing-assistant-feature-list">
                <div className="if-landing-assistant-feature">
                  <BadgeCheck size={16} />
                  <span>Understand coverage, premiums, and add-ons in plain language</span>
                </div>
                <div className="if-landing-assistant-feature">
                  <MessageSquareText size={16} />
                  <span>Move from quote questions to next steps without leaving the flow</span>
                </div>
                <div className="if-landing-assistant-feature">
                  <Mic size={16} />
                  <span>Use voice support when you want a guided, hands-free conversation</span>
                </div>
              </div>
            </div>

            <div className="if-landing-assistant-preview">
              <div className="if-chatbot-data-card if-landing-chat-preview-card">
                <div className="if-chatbot-header if-landing-chat-preview-header">
                  <div className="if-chatbot-header-icon">
                    <Sparkles size={16} />
                  </div>
                  <div className="if-chatbot-header-title">
                    <strong>InsureFlow Assistant</strong>
                    <span>Illustrative preview</span>
                  </div>
                </div>

                <div className="if-chatbot-messages if-landing-chat-preview-body">
                  <div className="if-chatbot-message">
                    <div className="if-chatbot-message-row">
                      <div className="if-chatbot-avatar">IF</div>
                      <p>I can help compare plans, explain add-ons, and guide you to payment.</p>
                    </div>
                  </div>

                  <div className="if-chatbot-message if-chatbot-message-user">
                    <div className="if-chatbot-message-row">
                      <p>I want to insure my car and understand zero-depreciation cover.</p>
                    </div>
                  </div>

                  <div className="if-chatbot-chip-row">
                    <span className="if-chatbot-chip">Quote guidance</span>
                    <span className="if-chatbot-chip">Add-on explanation</span>
                    <span className="if-chatbot-chip">Payment help</span>
                  </div>
                </div>

                <div className="if-landing-voice-preview">
                  <div className="if-voice-orb is-bot-speaking">
                    <div className="if-voice-orb-ring if-voice-orb-ring-1" />
                    <div className="if-voice-orb-ring if-voice-orb-ring-2" />
                    <div className="if-voice-orb-ring if-voice-orb-ring-3" />
                    <div className="if-voice-orb-core">
                      <Mic size={18} />
                    </div>
                  </div>
                  <div className="if-voice-transcript-line">
                    <span className="if-voice-transcript-label">Voice preview</span>
                    <span className="if-voice-transcript-text">
                      “Tell me the difference between base cover and recommended add-ons.”
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
