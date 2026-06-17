import { Bell, Blocks, FileStack, LayoutDashboard, RefreshCcw, Shield } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "./components/ui/Button";
import { StatusBadge } from "./components/ui/StatusBadge";
import { LayoutShell } from "./layouts/LayoutShell";
import { ProviderAdminLoginScreen } from "./pages/ProviderAdminLoginScreen";
import { ProviderBrokerManagementScreen } from "./pages/ProviderBrokerManagementScreen";
import { ProviderDashboardScreen } from "./pages/ProviderDashboardScreen";
import { ProviderPolicyLookupScreen } from "./pages/ProviderPolicyLookupScreen";
import { ProviderRegistryOverviewScreen } from "./pages/ProviderRegistryOverviewScreen";
import { ProviderSyncOperationsScreen } from "./pages/ProviderSyncOperationsScreen";
import { authStore } from "./store/authStore";

type ProviderAdminScreen = "dashboard" | "providers" | "brokers" | "sync" | "policies";

interface AppHistoryState {
  providerScreen: ProviderAdminScreen;
}

export default function App() {
  const [providerScreen, setProviderScreen] = useState<ProviderAdminScreen>("dashboard");
  const [providerAdminToken, setProviderAdminToken] = useState(
    authStore.getState().providerAdminToken,
  );

  const buildHistoryState = (
    overrides: Partial<AppHistoryState> = {},
  ): AppHistoryState => ({
    providerScreen,
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

  const navigateProviderScreen = (
    nextScreen: ProviderAdminScreen,
    options?: { replace?: boolean },
  ) => {
    setProviderScreen(nextScreen);
    syncHistory(buildHistoryState({ providerScreen: nextScreen }), options);
  };

  useEffect(() => {
    return authStore.subscribe((state) => {
      setProviderAdminToken(state.providerAdminToken);
    });
  }, []);

  useEffect(() => {
    const initialState = window.history.state as AppHistoryState | null;
    if (!initialState || !initialState.providerScreen) {
      syncHistory(buildHistoryState(), { replace: true });
    }

    const handlePopState = (event: PopStateEvent) => {
      const state = event.state as AppHistoryState | null;
      if (!state) return;
      setProviderScreen(state.providerScreen);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navItems = useMemo(
    () => [
      {
        label: "Dashboard",
        icon: LayoutDashboard,
        active: providerScreen === "dashboard",
        onClick: () => navigateProviderScreen("dashboard"),
      },
      {
        label: "Providers",
        icon: Blocks,
        active: providerScreen === "providers",
        onClick: () => navigateProviderScreen("providers"),
      },
      {
        label: "Brokers",
        icon: Shield,
        active: providerScreen === "brokers",
        onClick: () => navigateProviderScreen("brokers"),
      },
      {
        label: "Sync Center",
        icon: RefreshCcw,
        active: providerScreen === "sync",
        onClick: () => navigateProviderScreen("sync"),
      },
      {
        label: "Policies",
        icon: FileStack,
        active: providerScreen === "policies",
        onClick: () => navigateProviderScreen("policies"),
      },
    ],
    [providerScreen],
  );

  if (!providerAdminToken) {
    return <ProviderAdminLoginScreen />;
  }

  return (
    <LayoutShell
      brandName="InsureFlow Provider"
      navProps={{
        notificationCount: 2,
        rightSlot: (
          <>
            <StatusBadge status="admin">Provider Admin</StatusBadge>
            <Button variant="ghost" iconOnly ariaLabel="Notifications">
              <Bell size={18} />
            </Button>
            <button className="if-avatar-button" type="button" aria-label="Open provider admin menu">
              PA
            </button>
            <Button variant="ghost" onClick={() => authStore.clear()}>
              Sign out
            </Button>
          </>
        ),
      }}
      sidebarProps={{
        title: "Provider Console",
        items: navItems,
      }}
    >
      {providerScreen === "dashboard" ? (
        <ProviderDashboardScreen onNavigate={(screen) => navigateProviderScreen(screen)} />
      ) : null}
      {providerScreen === "providers" ? <ProviderRegistryOverviewScreen /> : null}
      {providerScreen === "brokers" ? <ProviderBrokerManagementScreen /> : null}
      {providerScreen === "sync" ? <ProviderSyncOperationsScreen /> : null}
      {providerScreen === "policies" ? <ProviderPolicyLookupScreen /> : null}
    </LayoutShell>
  );
}
