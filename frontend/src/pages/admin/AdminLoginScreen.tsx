import { useEffect, useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { OTPInput } from "../../components/ui/OTPInput";
import { PasswordField } from "../../components/ui/PasswordField";
import { StatusBadge } from "../../components/ui/StatusBadge";
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
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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

  const handleCredentialSubmit = async () => {
    await signInAction.run(async () => {
      try {
        await adminApi.login(email, password);
        setErrorMessage("");
        setOtpCode("");
        setCooldown(30);
        setStep("otp");
      } catch (error) {
        setErrorMessage(normalizeApiError(error).message);
      }
    });
  };

  const handleOtpVerification = async () => {
    await verifyAction.run(async () => {
      try {
        const payload = await adminApi.verifyLogin(email, otpCode);
        authStore.setToken("admin", payload.token.access_token);
        setErrorMessage("");
      } catch (error) {
        setErrorMessage(normalizeApiError(error).message);
      }
    });
  };

  const handleResendCode = async () => {
    await signInAction.run(async () => {
      try {
        await adminApi.login(email, password);
        setErrorMessage("");
        setOtpCode("");
        setCooldown(30);
      } catch (error) {
        setErrorMessage(normalizeApiError(error).message);
      }
    });
  };

  return (
    <div className="if-admin-auth-shell">
      <div className="if-admin-auth-card">
        <div className="if-admin-auth-brand" style={{ fontSize: "22px", margin: "0 auto var(--space-2)", textAlign: "center" }}>
          InsureFlow
        </div>
        <div style={{ display: "flex", justifyContent: "center", marginBottom: "var(--space-6)" }}>
          <StatusBadge status="admin">Admin</StatusBadge>
        </div>

        {step === "credentials" ? (
          <>
            <h2
              style={{
                fontSize: "22px",
                color: "var(--if-text-1)",
                textAlign: "center",
                marginBottom: "var(--space-6)",
                marginTop: 0,
              }}
            >
              Sign in to admin
            </h2>
            <div className="if-form-stack">
              <TextInput
                label="Email"
                onChange={(event) => {
                  setEmail(event.target.value);
                  if (errorMessage) {
                    setErrorMessage("");
                  }
                }}
                placeholder="Enter admin email"
                value={email}
                type="email"
              />
              <PasswordField
                label="Password"
                onChange={(event) => {
                  setPassword(event.target.value);
                  if (errorMessage) {
                    setErrorMessage("");
                  }
                }}
                placeholder="Enter password"
                value={password}
              />
              {errorMessage ? <span className="if-error-text" style={{ marginTop: "4px", display: "block" }}>{errorMessage}</span> : null}
              <Button
                className="if-button-full"
                loading={signInAction.isLoading}
                onClick={() => void handleCredentialSubmit()}
              >
                Sign in
              </Button>
            </div>
          </>
        ) : null}

        {step === "otp" ? (
          <>
            <h2
              style={{
                fontSize: "22px",
                color: "var(--if-text-1)",
                textAlign: "center",
                marginBottom: "var(--space-2)",
                marginTop: 0,
              }}
            >
              Two-factor verification
            </h2>
            <p className="if-inline-subtitle" style={{ fontSize: "14px", color: "var(--if-text-2)", textAlign: "center", marginBottom: "var(--space-6)", marginTop: 0 }}>
              Enter the 6-digit code sent to your registered email.
            </p>
            <div className="if-form-stack">
              <OTPInput
                label="Verification code"
                onChange={(value) => {
                  setOtpCode(value);
                  if (errorMessage) {
                    setErrorMessage("");
                  }
                }}
                value={otpCode}
              />
              {errorMessage ? <span className="if-error-text" style={{ marginTop: "4px", display: "block" }}>{errorMessage}</span> : null}
              <Button
                className="if-button-full"
                loading={verifyAction.isLoading}
                onClick={() => void handleOtpVerification()}
              >
                Verify
              </Button>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px" }}>
                <button
                  className="if-link-button"
                  onClick={() => {
                    setStep("credentials");
                    setOtpCode("");
                    setErrorMessage("");
                    setCooldown(30);
                  }}
                  style={{
                    color: "var(--if-text-2)",
                    fontFamily: "inherit",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    padding: 0,
                  }}
                  type="button"
                >
                  Back to sign in
                </button>
                <button
                  className="if-link-button"
                  disabled={cooldown > 0 || signInAction.isLoading}
                  onClick={() => void handleResendCode()}
                  style={{
                    color: "var(--if-cyan)",
                    fontFamily: "var(--fs-mono)",
                    background: "transparent",
                    border: "none",
                    cursor: cooldown > 0 || signInAction.isLoading ? "not-allowed" : "pointer",
                    padding: 0,
                  }}
                  type="button"
                >
                  Resend code {cooldown > 0 ? `(${cooldownLabel})` : ""}
                </button>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
