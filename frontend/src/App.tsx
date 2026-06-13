import {
  Bell,
  Blocks,
  ClipboardList,
  CreditCard,
  FileStack,
  LayoutDashboard,
  ListOrdered,
} from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "./components/ui/Button";
import { LayoutShell } from "./layouts/LayoutShell";
import { AdminDashboardScreen } from "./pages/admin/AdminDashboardScreen";
import { AdminLoginScreen } from "./pages/admin/AdminLoginScreen";
import { AdminRecordsScreen } from "./pages/admin/AdminRecordsScreen";
import { AdminTicketsScreen } from "./pages/admin/AdminTicketsScreen";
import { BrokerManagementScreen } from "./pages/admin/BrokerManagementScreen";
import { StatusBadge } from "./components/ui/StatusBadge";

type AdminScreen =
  | "dashboard"
  | "brokers"
  | "transactions"
  | "policies"
  | "payments"
  | "tickets";

/**
 * App mounts the admin-facing InsureFlow preview for this feature branch.
 * It shows the login flow first and then the sidebar-driven admin workspace.
 */
export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [screen, setScreen] = useState<AdminScreen>("dashboard");

  const adminNavItems = useMemo(
    () => [
      { label: "Dashboard", icon: LayoutDashboard, active: screen === "dashboard", onClick: () => setScreen("dashboard") },
      { label: "Brokers", icon: Blocks, active: screen === "brokers", onClick: () => setScreen("brokers") },
      { label: "Transactions", icon: ListOrdered, active: screen === "transactions", onClick: () => setScreen("transactions") },
      { label: "Policies", icon: FileStack, active: screen === "policies", onClick: () => setScreen("policies") },
      { label: "Payments", icon: CreditCard, active: screen === "payments", onClick: () => setScreen("payments") },
      { label: "Tickets", icon: ClipboardList, active: screen === "tickets", onClick: () => setScreen("tickets") },
    ],
    [screen],
  );

  if (!isAuthenticated) {
    return <AdminLoginScreen onLoginComplete={() => setIsAuthenticated(true)} />;
  }

  return (
    <LayoutShell
      navProps={{
        notificationCount: 4,
        rightSlot: (
          <>
            <StatusBadge status="admin">Admin</StatusBadge>
            <Button variant="ghost" iconOnly ariaLabel="Notifications">
              <Bell size={18} />
            </Button>
            <button className="if-avatar-button" type="button" aria-label="Open admin menu">
              AD
            </button>
          </>
        ),
      }}
      sidebarProps={{
        title: "Admin Console",
        items: adminNavItems,
      }}
    >
      {screen === "dashboard" ? <AdminDashboardScreen /> : null}
      {screen === "brokers" ? <BrokerManagementScreen /> : null}
      {screen === "transactions" ? <AdminRecordsScreen view="transactions" /> : null}
      {screen === "policies" ? <AdminRecordsScreen view="policies" /> : null}
      {screen === "payments" ? <AdminRecordsScreen view="payments" /> : null}
      {screen === "tickets" ? <AdminTicketsScreen /> : null}
    </LayoutShell>
  );
}
