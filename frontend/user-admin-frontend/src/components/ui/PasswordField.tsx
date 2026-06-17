import { Eye, EyeOff } from "lucide-react";
import { useId, useState } from "react";
import type { InputHTMLAttributes } from "react";

interface PasswordFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

/**
 * PasswordField adds a reveal toggle while preserving the shared floating-label style.
 * Admin auth uses it so password entry matches the rest of the form system.
 */
export function PasswordField({
  id,
  label,
  error,
  className = "",
  ...props
}: PasswordFieldProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="if-field">
      <div className="if-field-control">
        <input
          {...props}
          className={["if-input", "if-input-has-action", error ? "if-input-error" : "", className]
            .filter(Boolean)
            .join(" ")}
          id={inputId}
          placeholder={props.placeholder ?? " "}
          type={isVisible ? "text" : "password"}
        />
        <label className="if-floating-label" htmlFor={inputId}>
          {label}
        </label>
        <button
          aria-label={isVisible ? "Hide password" : "Show password"}
          className="if-input-action"
          onClick={() => setIsVisible((current) => !current)}
          type="button"
        >
          {isVisible ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>
      {error ? <span className="if-error-text">{error}</span> : null}
    </div>
  );
}
