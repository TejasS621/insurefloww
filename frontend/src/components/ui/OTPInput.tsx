import { useId, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";

interface OTPInputProps {
  label: string;
  length?: number;
  value?: string;
  onChange?: (value: string) => void;
}

/**
 * OTPInput renders segmented OTP boxes with auto-advance behavior.
 * It is intended for the shared auth experience, not a one-off screen.
 */
export function OTPInput({ label, length = 6, value, onChange }: OTPInputProps) {
  const baseId = useId();
  const [internalDigits, setInternalDigits] = useState<string[]>(() => Array.from({ length }, () => ""));
  const refs = useRef<Array<HTMLInputElement | null>>([]);
  const digits = value
    ? value.padEnd(length, " ").slice(0, length).split("").map((digit) => (digit === " " ? "" : digit))
    : internalDigits;

  const handleChange = (index: number, event: ChangeEvent<HTMLInputElement>) => {
    const nextValue = event.target.value.replace(/\D/g, "").slice(-1);
    const nextDigits = [...digits];
    nextDigits[index] = nextValue;
    setInternalDigits(nextDigits);
    onChange?.(nextDigits.join(""));

    if (nextValue && index < length - 1) {
      refs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Backspace" && !digits[index] && index > 0) {
      refs.current[index - 1]?.focus();
    }
  };

  return (
    <fieldset className="if-otp-fieldset">
      <div className="if-field">
        <span className="if-helper-text">{label}</span>
        <div className="if-otp-row" role="group" aria-label={label}>
          {digits.map((digit, index) => (
            <input
              key={`${baseId}-${index}`}
              ref={(element) => {
                refs.current[index] = element;
              }}
              aria-label={`${label} digit ${index + 1}`}
              className="if-otp-input"
              inputMode="numeric"
              maxLength={1}
              onChange={(event) => handleChange(index, event)}
              onKeyDown={(event) => handleKeyDown(index, event)}
              type="text"
              value={digit}
            />
          ))}
        </div>
      </div>
    </fieldset>
  );
}
