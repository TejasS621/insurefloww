import { ChevronDown } from "lucide-react";
import { useId } from "react";
import type { SelectHTMLAttributes } from "react";

interface SelectOption {
  label: string;
  value: string;
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: SelectOption[];
  error?: string;
}

/**
 * SelectField keeps dropdowns aligned with the shared floating-label form style.
 * Customer flow screens use it for coverage, tenure, and relationship fields.
 */
export function SelectField({
  id,
  label,
  options,
  error,
  className = "",
  ...props
}: SelectFieldProps) {
  const generatedId = useId();
  const selectId = id ?? generatedId;

  return (
    <div className="if-field">
      <div className="if-field-control">
        <select
          {...props}
          className={[
            "if-input",
            "if-select",
            error ? "if-input-error" : "",
            className,
          ]
            .filter(Boolean)
            .join(" ")}
          defaultValue={props.defaultValue ?? ""}
          id={selectId}
        >
          <option value="" disabled hidden>
            Select
          </option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <label className="if-floating-label" htmlFor={selectId}>
          {label}
        </label>
        <ChevronDown className="if-select-icon" size={18} />
      </div>
      {error ? <span className="if-error-text">{error}</span> : null}
    </div>
  );
}
