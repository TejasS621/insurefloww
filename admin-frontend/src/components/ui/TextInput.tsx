import { useId } from "react";
import type { InputHTMLAttributes } from "react";

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
  mono?: boolean;
}

/**
 * TextInput provides floating-label fields with inline validation.
 * It keeps inputs visually consistent across auth, policy, and admin flows.
 */
export function TextInput({
  id,
  label,
  error,
  helperText,
  mono = false,
  className = "",
  ...props
}: TextInputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;

  return (
    <div className="if-field">
      <div className="if-field-control">
        <input
          {...props}
          className={[
            "if-input",
            mono ? "if-input-mono" : "",
            error ? "if-input-error" : "",
            className,
          ]
            .filter(Boolean)
            .join(" ")}
          id={inputId}
          placeholder={props.placeholder ?? " "}
        />
        <label className="if-floating-label" htmlFor={inputId}>
          {label}
        </label>
      </div>
      {error ? <span className="if-error-text">{error}</span> : null}
      {!error && helperText ? <span className="if-helper-text">{helperText}</span> : null}
    </div>
  );
}
