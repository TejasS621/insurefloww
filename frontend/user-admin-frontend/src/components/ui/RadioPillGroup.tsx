interface RadioPillOption {
  label: string;
  value: string;
}

interface RadioPillGroupProps {
  label: string;
  options: RadioPillOption[];
  value: string;
  onChange: (value: string) => void;
}

/**
 * RadioPillGroup renders compact pill-style selections for small choice sets.
 * It is useful for gender and priority inputs in customer-facing forms.
 */
export function RadioPillGroup({
  label,
  options,
  value,
  onChange,
}: RadioPillGroupProps) {
  return (
    <div className="if-field">
      <span className="if-group-label">{label}</span>
      <div className="if-pill-group" role="radiogroup" aria-label={label}>
        {options.map((option) => (
          <button
            key={option.value}
            aria-checked={value === option.value}
            className={`if-pill ${value === option.value ? "is-active" : ""}`}
            onClick={() => onChange(option.value)}
            role="radio"
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
