import { useId } from "react";
import type { TextareaHTMLAttributes } from "react";

interface TextareaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
}

/**
 * TextareaField extends the shared floating-label language to multiline input.
 * It is used for support tickets without introducing form-specific styling.
 */
export function TextareaField({
  id,
  label,
  error,
  className = "",
  ...props
}: TextareaFieldProps) {
  const generatedId = useId();
  const textareaId = id ?? generatedId;

  return (
    <div className="if-field">
      <div className="if-field-control">
        <textarea
          {...props}
          className={[
            "if-input",
            "if-textarea",
            error ? "if-input-error" : "",
            className,
          ]
            .filter(Boolean)
            .join(" ")}
          id={textareaId}
          placeholder={props.placeholder ?? " "}
        />
        <label className="if-floating-label" htmlFor={textareaId}>
          {label}
        </label>
      </div>
      {error ? <span className="if-error-text">{error}</span> : null}
    </div>
  );
}
