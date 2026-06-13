import { Bell, FileText, Home, LifeBuoy, Shield, UserRound } from "lucide-react";

import { Button } from "./components/ui/Button";
import { EmptyState } from "./components/ui/EmptyState";
import { OTPInput } from "./components/ui/OTPInput";
import { Skeleton } from "./components/ui/Skeleton";
import { StatCard } from "./components/ui/StatCard";
import { StatusBadge } from "./components/ui/StatusBadge";
import { TextInput } from "./components/ui/TextInput";
import { LayoutShell } from "./layouts/LayoutShell";
import { formatCurrencyINR } from "./utils/formatters";

const adminNavItems = [
  { label: "Dashboard", icon: Home, active: true },
  { label: "Policies", icon: Shield },
  { label: "Tickets", icon: LifeBuoy },
  { label: "Profile", icon: UserRound },
];

const customerBottomTabs = [
  { label: "Home", icon: Home, active: true },
  { label: "Policies", icon: FileText },
  { label: "Tickets", icon: LifeBuoy },
  { label: "Profile", icon: UserRound },
];

/**
 * App renders the foundational design-system shell only.
 * It exists as a living import target until product screens are added.
 */
export default function App() {
  return (
    <LayoutShell
      navProps={{
        notificationCount: 3,
        rightSlot: (
          <>
            <StatusBadge status="admin">Admin</StatusBadge>
            <Button variant="ghost" iconOnly ariaLabel="Notifications">
              <Bell size={18} />
            </Button>
            <button className="if-avatar-button" type="button" aria-label="Open user menu">
              TR
            </button>
          </>
        ),
      }}
      sidebarProps={{
        title: "Admin Console",
        items: adminNavItems,
      }}
      bottomNavProps={{
        items: customerBottomTabs,
      }}
    >
      <section className="if-hero-card">
        <div>
          <p className="if-eyebrow">Design Foundation</p>
          <h1 className="if-hero-title">InsureFlow layout shell and shared UI system</h1>
          <p className="if-hero-copy">
            This branch sets up reusable tokens, navigation, form controls, feedback states, and
            admin or customer layout primitives for the rest of the frontend.
          </p>
        </div>
        <div className="if-hero-actions">
          <Button>Primary Action</Button>
          <Button variant="ghost">Ghost Action</Button>
        </div>
      </section>

      <section className="if-grid if-grid-stats">
        <StatCard label="Active Policies" value="1,248" />
        <StatCard label="Premium Volume" value={formatCurrencyINR(1200000)} variant="navy" />
        <StatCard label="Pending Reviews" value="86" />
      </section>

      <section className="if-grid if-grid-two">
        <div className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Inputs</p>
              <h2>Form primitives</h2>
            </div>
            <StatusBadge status="processing">Processing</StatusBadge>
          </div>
          <div className="if-form-stack">
            <TextInput id="phone" label="Mobile Number" placeholder="Enter mobile number" />
            <TextInput
              id="quote-reference"
              label="Quote Reference"
              placeholder="QUO-HLT-20260613-01"
              mono
              helperText="All references and policy numbers use JetBrains Mono."
            />
            <TextInput
              id="inline-error"
              label="PAN Number"
              placeholder="ABCDE1234F"
              error="This field demonstrates inline validation styling."
            />
            <OTPInput label="OTP Verification" />
          </div>
        </div>

        <div className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Feedback</p>
              <h2>Status and loading</h2>
            </div>
          </div>
          <div className="if-badge-row">
            <StatusBadge status="issued">Policy Issued</StatusBadge>
            <StatusBadge status="pending">Pending</StatusBadge>
            <StatusBadge status="failed">Payment Failed</StatusBadge>
            <StatusBadge status="processing">Processing</StatusBadge>
            <StatusBadge status="cancelled">Cancelled</StatusBadge>
          </div>
          <div className="if-skeleton-stack">
            <Skeleton height={76} />
            <Skeleton height={18} width="72%" />
            <Skeleton height={18} width="55%" />
          </div>
        </div>
      </section>

      <section className="if-surface-card">
        <EmptyState
          title="No screen mounted yet"
          description="Feature pages can import this system without bringing their own layout, input styles, badges, or loading states."
          action={<Button>Use as base shell</Button>}
        />
      </section>
    </LayoutShell>
  );
}
