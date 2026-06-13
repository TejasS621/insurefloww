import { useEffect, useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { OTPInput } from "../../components/ui/OTPInput";
import { PasswordField } from "../../components/ui/PasswordField";
import { TextInput } from "../../components/ui/TextInput";

interface AdminLoginScreenProps {
  onLoginComplete: () => void;
}

/**
 * AdminLoginScreen handles credential sign-in and the follow-up OTP verification step.
 * It intentionally omits the sidebar so authentication remains focused and distraction-free.
 */
export function AdminLoginScreen({ onLoginComplete }: AdminLoginScreenProps) {
  const [step, setStep] = useState<"credentials" | "otp">("credentials");
  const [cooldown, setCooldown] = useState(30);
  const cooldownLabel = useMemo(() => `${cooldown}s`, [cooldown]);

  useEffect(() => {
    if (step !== "otp" || cooldown <= 0) {
      return undefined;
    }
    const timer = window.setTimeout(() => setCooldown((current) => current - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [cooldown, step]);

  return (
    <div className="if-admin-auth-shell">
      <div className="if-admin-auth-card">
        <div className="if-admin-auth-brand">InsureFlow</div>

        {step === "credentials" ? (
          <>
            <h2>Admin sign in</h2>
            <div className="if-form-stack">
              <TextInput label="Email" placeholder="admin@insurefloww.com" />
              <PasswordField label="Password" placeholder="Enter password" />
              <Button className="if-button-full" onClick={() => setStep("otp")}>
                Sign in
              </Button>
            </div>
          </>
        ) : null}

        {step === "otp" ? (
          <>
            <h2>Two-factor verification</h2>
            <p className="if-inline-subtitle">
              Enter the 6-digit code sent to your registered email.
            </p>
            <div className="if-form-stack">
              <OTPInput label="Verification code" />
              <Button className="if-button-full" onClick={onLoginComplete}>
                Verify
              </Button>
              <button
                className="if-link-button"
                disabled={cooldown > 0}
                onClick={() => setCooldown(30)}
                type="button"
              >
                Resend code {cooldown > 0 ? `(${cooldownLabel})` : ""}
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
