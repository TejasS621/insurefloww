import {
  Bell,
  Blocks,
  Building2,
  ClipboardList,
  CreditCard,
  FileStack,
  LayoutDashboard,
  ListOrdered,
  Shield,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "./components/ui/Button";
import { StatusBadge } from "./components/ui/StatusBadge";
import { LayoutShell } from "./layouts/LayoutShell";
import { AdminDashboardScreen } from "./pages/AdminDashboardScreen";
import { AdminLoginScreen } from "./pages/AdminLoginScreen";
import { AdminRecordsScreen } from "./pages/AdminRecordsScreen";
import { AdminTicketsScreen } from "./pages/AdminTicketsScreen";
import { BrokerManagementScreen } from "./pages/BrokerManagementScreen";
import { ProviderManagementScreen } from "./pages/ProviderManagementScreen";
import { authStore } from "./store/authStore";

type AdminScreen =
  | "dashboard"
  | "brokers"
  | "providers"
  | "transactions"
  | "policies"
  | "payments"
  | "tickets";

interface AppHistoryState {
  adminScreen: AdminScreen;
}

/**
 * App is the admin portal entry point.
 * It manages the admin auth session and routes between all admin screens
 * using the window.history state machine pattern.
 */
export default function App() {
  const [adminScreen, setAdminScreen] = useState<AdminScreen>("dashboard");
  const [adminToken, setAdminToken] = useState<string | null>(authStore.getState().adminToken);

  const buildHistoryState = (overrides: Partial<AppHistoryState> = {}): AppHistoryState => ({
    adminScreen,
    ...overrides,
  });

  const syncHistory = (nextState: AppHistoryState, options?: { replace?: boolean }) => {
    if (typeof window === "undefined") return;
    if (options?.replace) {
      window.history.replaceState(nextState, "");
      return;
    }
    window.history.pushState(nextState, "");
  };

  const navigateAdminScreen = (nextScreen: AdminScreen, options?: { replace?: boolean }) => {
    setAdminScreen(nextScreen);
    syncHistory(buildHistoryState({ adminScreen: nextScreen }), options);
  };

  useEffect(() => {
    return authStore.subscribe((state) => {
      setAdminToken(state.adminToken);
    });
  }, []);

  useEffect(() => {
    const initialState = window.history.state as AppHistoryState | null;
    if (!initialState || !initialState.adminScreen) {
      syncHistory(buildHistoryState(), { replace: true });
    }

    const handlePopState = (event: PopStateEvent) => {
      const state = event.state as AppHistoryState | null;
      if (!state) return;
      setAdminScreen(state.adminScreen);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const adminNavItems = useMemo(
    () => [
      {
        label: "Dashboard",
        icon: LayoutDashboard,
        active: adminScreen === "dashboard",
        onClick: () => navigateAdminScreen("dashboard"),
      },
      {
        label: "Brokers",
        icon: Shield,
        active: adminScreen === "brokers",
        onClick: () => navigateAdminScreen("brokers"),
      },
      {
        label: "Providers",
        icon: Building2,
        active: adminScreen === "providers",
        onClick: () => navigateAdminScreen("providers"),
      },
      {
        label: "Transactions",
        icon: ListOrdered,
        active: adminScreen === "transactions",
        onClick: () => navigateAdminScreen("transactions"),
      },
      {
        label: "Policies",
        icon: FileStack,
        active: adminScreen === "policies",
        onClick: () => navigateAdminScreen("policies"),
      },
      {
        label: "Payments",
        icon: CreditCard,
        active: adminScreen === "payments",
        onClick: () => navigateAdminScreen("payments"),
      },
      {
        label: "Tickets",
        icon: ClipboardList,
        active: adminScreen === "tickets",
        onClick: () => navigateAdminScreen("tickets"),
      },
    ],
    [adminScreen],
  );

  // Show login screen when not authenticated
  if (!adminToken) {
    return <AdminLoginScreen />;
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
            <Button
              variant="ghost"
              onClick={() => authStore.clear("admin")}
            >
              Sign out
            </Button>
          </>
        ),
      }}
      sidebarProps={{
        title: "Admin Console",
        items: adminNavItems,
      }}
    >
      {adminScreen === "dashboard" ? (
        <AdminDashboardScreen onNavigate={(screen) => navigateAdminScreen(screen)} />
      ) : null}
      {adminScreen === "brokers" ? <BrokerManagementScreen /> : null}
      {adminScreen === "providers" ? <ProviderManagementScreen /> : null}
      {adminScreen === "transactions" ? <AdminRecordsScreen view="transactions" /> : null}
      {adminScreen === "policies" ? <AdminRecordsScreen view="policies" /> : null}
      {adminScreen === "payments" ? <AdminRecordsScreen view="payments" /> : null}
      {adminScreen === "tickets" ? <AdminTicketsScreen /> : null}
    </LayoutShell>
  );
}
