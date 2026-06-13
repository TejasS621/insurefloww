interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  ariaLabel: string;
}

/**
 * ToggleSwitch provides a compact on or off control for add-on selections.
 * It keeps quote enhancement rows consistent with the shared visual system.
 */
export function ToggleSwitch({ checked, onChange, ariaLabel }: ToggleSwitchProps) {
  return (
    <button
      aria-label={ariaLabel}
      aria-pressed={checked}
      className={`if-switch ${checked ? "is-on" : ""}`}
      onClick={() => onChange(!checked)}
      type="button"
    >
      <span className="if-switch-thumb" />
    </button>
  );
}
