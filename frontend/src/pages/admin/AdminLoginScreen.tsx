import { useEffect, useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { OTPInput } from "../../components/ui/OTPInput";
import { PasswordField } from "../../components/ui/PasswordField";
import { TextInput } from "../../components/ui/TextInput";
import { useAsyncAction } from "../../hooks/useAsyncAction";
import { adminApi } from "../../services/api/admin";
import { authStore } from "../../store/authStore";
import { normalizeApiError } from "../../utils/apiErrors";

/**
 * AdminLoginScreen handles credential sign-in and the follow-up OTP verification step.
 * It intentionally omits the sidebar so authentication remains focused and distraction-free.
 */
export function AdminLoginScreen() {
  const [step, setStep] = useState<"credentials" | "otp">("credentials");
  const [cooldown, setCooldown] = useState(30);
  const [email, setEmail] = useState("admin@insurefloww.com");
  const [password, setPassword] = useState("Admin@12345");
  const [otpCode, setOtpCode] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const cooldownLabel = useMemo(() => `${cooldown}s`, [cooldown]);
  const signInAction = useAsyncAction();
  const verifyAction = useAsyncAction();

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
              <TextInput
                label="Email"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="admin@insurefloww.com"
                value={email}
              />
              <PasswordField
                label="Password"
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter password"
                value={password}
              />
              {errorMessage ? <ErrorCard message={errorMessage} /> : null}
              <Button
                className="if-button-full"
                loading={signInAction.isLoading}
                onClick={() =>
                  void signInAction.run(async () => {
                    try {
                      await adminApi.login(email, password);
                      setErrorMessage("");
                      setStep("otp");
                    } catch (error) {
                      setErrorMessage(normalizeApiError(error).message);
                    }
                  })
                }
              >
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
              <OTPInput label="Verification code" onChange={setOtpCode} value={otpCode} />
              {errorMessage ? <ErrorCard message={errorMessage} /> : null}
              <Button
                className="if-button-full"
                loading={verifyAction.isLoading}
                onClick={() =>
                  void verifyAction.run(async () => {
                    try {
                      const payload = await adminApi.verifyLogin(email, otpCode);
                      authStore.setToken("admin", payload.token.access_token);
                      setErrorMessage("");
                    } catch (error) {
                      setErrorMessage(normalizeApiError(error).message);
                    }
                  })
                }
              >
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
