import { Menu, X, Sun, Moon } from "lucide-react";
import { useMemo, useState, useEffect } from "react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { themeStore } from "../store/themeStore";

interface NavItem {
  label: string;
  icon: LucideIcon;
  active?: boolean;
  onClick?: () => void;
}

interface LayoutShellProps {
  children: ReactNode;
  navProps?: {
    notificationCount?: number;
    rightSlot?: ReactNode;
    mobileMenuItems?: NavItem[];
  };
  sidebarProps?: {
    title: string;
    items: NavItem[];
  };
  bottomNavProps?: {
    items: NavItem[];
  };
}

/**
 * LayoutShell composes the sticky navbar, admin sidebar, and mobile bottom nav.
 * It is the structural base that future customer and admin screens will mount into.
 */
export function LayoutShell({
  children,
  navProps,
  sidebarProps,
  bottomNavProps,
}: LayoutShellProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [theme, setTheme] = useState(themeStore.getTheme());

  useEffect(() => {
    return themeStore.subscribe((newTheme) => setTheme(newTheme));
  }, []);

  const mobileItems = useMemo(
    () => navProps?.mobileMenuItems ?? sidebarProps?.items ?? bottomNavProps?.items ?? [],
    [bottomNavProps?.items, navProps?.mobileMenuItems, sidebarProps?.items],
  );

  return (
    <div className="if-page-shell">
      <header className="if-navbar">
        <div className="if-content-shell if-navbar-inner">
          <div className="if-wordmark">InsureFlow</div>
          <div className="if-navbar-actions">
            {navProps?.notificationCount ? (
              <span className="if-badge if-badge-processing">
                {navProps.notificationCount} alerts
              </span>
            ) : null}
            <button
              className="if-theme-toggle"
              onClick={() => themeStore.toggleTheme()}
              type="button"
              aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
            >
              {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
            </button>
            {navProps?.rightSlot}
            {mobileItems.length ? (
              <button
                className="if-mobile-menu"
                onClick={() => setIsMobileMenuOpen(true)}
                type="button"
                aria-label="Open navigation menu"
              >
                <Menu size={18} />
              </button>
            ) : null}
          </div>
        </div>
      </header>

      {isMobileMenuOpen ? (
        <div className="if-mobile-drawer" role="dialog" aria-modal="true" aria-label="Navigation menu">
          <div className="if-mobile-drawer-header">
            <div className="if-wordmark">InsureFlow</div>
            <button
              className="if-mobile-drawer-close"
              onClick={() => setIsMobileMenuOpen(false)}
              type="button"
              aria-label="Close navigation menu"
            >
              <X size={20} />
            </button>
          </div>
          <nav className="if-mobile-drawer-nav">
            {mobileItems.map((item) => {
              const Icon = item.icon;
              return (
                  <button
                    key={item.label}
                    className={`if-mobile-drawer-item ${item.active ? "is-active" : ""}`}
                    onClick={() => {
                      item.onClick?.();
                      setIsMobileMenuOpen(false);
                    }}
                    type="button"
                  >
                  <Icon size={20} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      ) : null}

      <div className="if-main-layout">
        {sidebarProps ? (
          <aside className="if-sidebar">
            <p className="if-sidebar-title">{sidebarProps.title}</p>
            <nav className="if-sidebar-nav" aria-label="Admin navigation">
              {sidebarProps.items.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.label}
                    className={`if-sidebar-item ${item.active ? "is-active" : ""}`}
                    onClick={item.onClick}
                    type="button"
                  >
                    <Icon size={20} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </aside>
        ) : null}

        <main className="if-shell-content">
          <div className="if-content-shell">{children}</div>
        </main>
      </div>

      {bottomNavProps ? (
        <nav className="if-bottom-nav" aria-label="Customer mobile navigation">
          <div className="if-bottom-nav-grid">
            {bottomNavProps.items.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.label}
                  className={`if-bottom-nav-item ${item.active ? "is-active" : ""}`}
                  onClick={item.onClick}
                  type="button"
                >
                  <Icon size={24} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>
      ) : null}
    </div>
  );
}
