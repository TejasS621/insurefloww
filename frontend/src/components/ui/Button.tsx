import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
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
  iconOnly = false,
  ariaLabel,
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  const classes = [
    "if-button",
    variant === "primary" ? "if-button-primary" : "if-button-ghost",
    iconOnly ? "if-button-icon-only" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button {...props} aria-label={ariaLabel} className={classes} type={type}>
      {children}
    </button>
  );
}
