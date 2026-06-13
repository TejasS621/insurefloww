import { Bell, FileText, Home, LifeBuoy, UserRound } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "./components/ui/Button";
import { LayoutShell } from "./layouts/LayoutShell";
import { ApplicationFlowScreen } from "./pages/application/ApplicationFlowScreen";
import { CustomerDashboardScreen } from "./pages/dashboard/CustomerDashboardScreen";
import { LandingScreen } from "./pages/landing/LandingScreen";
import { PaymentInitiationScreen } from "./pages/payment/PaymentInitiationScreen";
import { QuoteComparisonScreen } from "./pages/quotes/QuoteComparisonScreen";
import { SupportTicketScreen } from "./pages/support/SupportTicketScreen";

type Screen =
  | "landing"
  | "application"
  | "quotes"
  | "payment"
  | "dashboard"
  | "support";

type InsuranceType = "health" | "vehicle" | "travel" | "home" | "life";

/**
 * App composes the customer-facing InsureFlow journey on top of the Phase 1 system.
 * It previews landing, application, quotes, payment, dashboard, and support screens.
 */
export default function App() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [selectedInsuranceType, setSelectedInsuranceType] = useState<InsuranceType>("health");

  const bottomNavItems = useMemo(
    () => [
      {
        label: "Home",
        icon: Home,
        active: screen === "landing" || screen === "application" || screen === "quotes" || screen === "payment",
        onClick: () => setScreen("landing"),
      },
      {
        label: "Policies",
        icon: FileText,
        active: screen === "dashboard",
        onClick: () => setScreen("dashboard"),
      },
      {
        label: "Tickets",
        icon: LifeBuoy,
        active: screen === "support",
        onClick: () => setScreen("support"),
      },
      {
        label: "Profile",
        icon: UserRound,
        active: false,
        onClick: () => setScreen("dashboard"),
      },
    ],
    [screen],
  );

  const handleSelectType = (type: InsuranceType) => {
    setSelectedInsuranceType(type);
    setScreen("application");
  };

  return (
    <LayoutShell
      navProps={{
        notificationCount: 2,
        rightSlot: (
          <>
            <Button variant="ghost" iconOnly ariaLabel="Notifications">
              <Bell size={18} />
            </Button>
            <button className="if-avatar-button" type="button" aria-label="Open user menu">
              TS
            </button>
          </>
        ),
      }}
      bottomNavProps={{
        items: bottomNavItems,
      }}
    >
      {screen === "landing" ? <LandingScreen onSelectType={handleSelectType} /> : null}
      {screen === "application" ? (
        <ApplicationFlowScreen
          insuranceType={selectedInsuranceType}
          onBackToLanding={() => setScreen("landing")}
          onSubmit={() => setScreen("quotes")}
        />
      ) : null}
      {screen === "quotes" ? (
        <QuoteComparisonScreen onBack={() => setScreen("application")} onProceed={() => setScreen("payment")} />
      ) : null}
      {screen === "payment" ? <PaymentInitiationScreen onProceed={() => setScreen("dashboard")} /> : null}
      {screen === "dashboard" ? <CustomerDashboardScreen onOpenSupport={() => setScreen("support")} /> : null}
      {screen === "support" ? <SupportTicketScreen /> : null}
    </LayoutShell>
  );
}
