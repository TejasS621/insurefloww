import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "ghost";
type ButtonSize = "default" | "large";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  iconOnly?: boolean;
  ariaLabel?: string;
}

/**
 * Button centralizes shared button styling and motion rules.
 * Product screens can consume it without redefining visual states.
 */
export function Button({
  children,
  variant = "primary",
  size = "default",
  loading = false,
  iconOnly = false,
  ariaLabel,
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  const classes = [
    "if-button",
    variant === "primary" ? "if-button-primary" : "if-button-ghost",
    size === "large" ? "if-button-large" : "",
    iconOnly ? "if-button-icon-only" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      {...props}
      aria-busy={loading}
      aria-label={ariaLabel}
      className={classes}
      disabled={props.disabled || loading}
      type={type}
    >
      {loading ? <span className="if-button-spinner" /> : null}
      <span className={loading ? "if-button-loading-text" : ""}>{children}</span>
    </button>
  );
}
