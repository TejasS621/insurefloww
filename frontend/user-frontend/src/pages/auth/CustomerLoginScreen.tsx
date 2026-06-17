import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { OTPInput } from "../../components/ui/OTPInput";
import { TextInput } from "../../components/ui/TextInput";

interface CustomerLoginScreenProps {
  mobileNumber: string;
  otpCode: string;
  otpRequested: boolean;
  otpError?: string;
  isSendingOtp: boolean;
  isVerifyingOtp: boolean;
  onBack: () => void;
  onMobileNumberChange: (value: string) => void;
  onOtpCodeChange: (value: string) => void;
  onSendOtp: () => Promise<void>;
  onVerifyOtp: () => Promise<void>;
}

/**
 * CustomerLoginScreen handles mobile OTP authentication before the application starts.
 * Keeping login separate removes auth controls from the application form and keeps the flow clearer.
 */
export function CustomerLoginScreen({
  mobileNumber,
  otpCode,
  otpRequested,
  otpError,
  isSendingOtp,
  isVerifyingOtp,
  onBack,
  onMobileNumberChange,
  onOtpCodeChange,
  onSendOtp,
  onVerifyOtp,
}: CustomerLoginScreenProps) {
  return (
    <div className="if-screen-stack">
      {otpError && !otpRequested ? <ErrorCard message={otpError} /> : null}

      <div style={{ margin: "0 auto", maxWidth: "520px", width: "100%" }}>
        <section className="if-surface-card">
          <div className="if-section-heading">
            <div>
              <p className="if-eyebrow">Customer Login</p>
              <h2>Verify your mobile number</h2>
              <p className="if-inline-subtitle">
                Sign in first, then continue with your insurance application.
              </p>
            </div>
          </div>

          <div className="if-form-stack">
            <TextInput
              label="Mobile Number"
              onChange={(event) => onMobileNumberChange(event.target.value)}
              placeholder="e.g. 7778889997"
              value={mobileNumber}
            />

            {!otpRequested ? (
              <Button className="if-button-full" loading={isSendingOtp} onClick={() => void onSendOtp()}>
                Send OTP
              </Button>
            ) : (
              <>
                <div className="if-field">
                  <OTPInput label="Enter 6-digit OTP" onChange={onOtpCodeChange} value={otpCode} />
                  {otpError ? (
                    <span className="if-error-text" style={{ display: "block", marginTop: "4px" }}>
                      {otpError}
                    </span>
                  ) : null}
                </div>
                <Button className="if-button-full" loading={isVerifyingOtp} onClick={() => void onVerifyOtp()}>
                  Verify and Continue
                </Button>
              </>
            )}
          </div>

          <footer
            className="if-form-footer"
            style={{ borderTop: "1px solid var(--if-border)", marginTop: "24px", paddingTop: "20px" }}
          >
            <Button onClick={onBack} variant="ghost">
              Back
            </Button>
          </footer>
        </section>
      </div>
    </div>
  );
}
