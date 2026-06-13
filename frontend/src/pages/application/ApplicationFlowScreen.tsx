import { useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { OTPInput } from "../../components/ui/OTPInput";
import { ProgressStepper } from "../../components/ui/ProgressStepper";
import { RadioPillGroup } from "../../components/ui/RadioPillGroup";
import { SelectField } from "../../components/ui/SelectField";
import { TextInput } from "../../components/ui/TextInput";
import type { ApplicationSummary, CustomerApplicationPayload } from "../../services/api/customer";

type InsuranceType = "HEALTH" | "LIFE" | "VEHICLE" | "TRAVEL" | "HOME";

interface ApplicationFlowScreenProps {
  insuranceType: InsuranceType;
  isAuthenticated: boolean;
  otpRequested: boolean;
  otpError?: string;
  formError?: string;
  isSendingOtp: boolean;
  isVerifyingOtp: boolean;
  isSubmitting: boolean;
  onBackToLanding: () => void;
  onSendOtp: (mobileNumber: string) => Promise<void>;
  onVerifyOtp: (mobileNumber: string, otpCode: string) => Promise<void>;
  onSubmit: (payload: CustomerApplicationPayload) => Promise<void>;
  resumedApplication: ApplicationSummary | null;
}

const coverageOptions = [
  { label: "₹5L", value: "500000" },
  { label: "₹10L", value: "1000000" },
  { label: "₹25L", value: "2500000" },
  { label: "₹50L", value: "5000000" },
  { label: "₹1Cr", value: "10000000" },
];

const tenureOptions = [
  { label: "1 year", value: "1" },
  { label: "2 years", value: "2" },
  { label: "3 years", value: "3" },
];

const relationshipOptions = [
  { label: "Spouse", value: "SPOUSE" },
  { label: "Parent", value: "PARENT" },
  { label: "Sibling", value: "FAMILY" },
  { label: "Child", value: "CHILD" },
];

const stepItems = [
  { title: "Personal Details" },
  { title: "Coverage Details" },
  { title: "Nominee Details" },
];

/**
 * ApplicationFlowScreen manages OTP verification and application submission.
 * It collects customer data locally and hands validated actions back to the API layer.
 */
export function ApplicationFlowScreen({
  insuranceType,
  isAuthenticated,
  otpRequested,
  otpError,
  formError,
  isSendingOtp,
  isVerifyingOtp,
  isSubmitting,
  onBackToLanding,
  onSendOtp,
  onVerifyOtp,
  onSubmit,
  resumedApplication,
}: ApplicationFlowScreenProps) {
  const [step, setStep] = useState(0);
  const [fullName, setFullName] = useState("Tejas Shah");
  const [mobileNumber, setMobileNumber] = useState("7778889997");
  const [otpCode, setOtpCode] = useState("");
  const [email, setEmail] = useState("tejas@example.com");
  const [dateOfBirth, setDateOfBirth] = useState("1998-10-04");
  const [gender, setGender] = useState<"MALE" | "FEMALE" | "OTHER">("MALE");
  const [coverageAmount, setCoverageAmount] = useState("1000000");
  const [tenureYears, setTenureYears] = useState("1");
  const [nomineeName, setNomineeName] = useState("Ananya Shah");
  const [nomineeRelationship, setNomineeRelationship] = useState("SPOUSE");
  const [nomineeDob, setNomineeDob] = useState("2000-11-19");
  const [nomineeMobile, setNomineeMobile] = useState("8887776665");
  const [conditions, setConditions] = useState<string[]>(["Diabetes"]);

  const displayInsuranceType = useMemo(
    () => insuranceType.charAt(0) + insuranceType.slice(1).toLowerCase(),
    [insuranceType],
  );

  const toggleCondition = (condition: string) => {
    setConditions((current) =>
      current.includes(condition)
        ? current.filter((item) => item !== condition)
        : [...current, condition],
    );
  };

  const handleNext = async () => {
    if (step === 0 && !isAuthenticated) {
      await onVerifyOtp(mobileNumber, otpCode);
      setStep(1);
      return;
    }

    if (step === 2) {
      await onSubmit({
        insuranceType,
        fullName,
        mobileNumber,
        email,
        dateOfBirth,
        gender,
        coverageAmount: Number(coverageAmount),
        tenureYears: Number(tenureYears),
        nomineeName,
        nomineeRelationship,
        nomineeDob,
        nomineeMobile,
        healthConditions: conditions,
      });
      return;
    }

    setStep((current) => current + 1);
  };

  return (
    <div className="if-screen-stack">
      {resumedApplication ? (
        <div className="if-resume-banner">
          <div>
            <strong>You have an active application. Continue where you left off.</strong>
          </div>
          <div className="if-resume-actions">
            <Button onClick={() => setStep(2)}>Resume</Button>
            <Button onClick={onBackToLanding} variant="ghost">
              Start New
            </Button>
          </div>
        </div>
      ) : null}

      {formError ? <ErrorCard message={formError} /> : null}

      <section className="if-surface-card">
        <ProgressStepper currentStep={step} steps={stepItems} />

        {step === 0 ? (
          <div className="if-screen-section">
            <div className="if-form-grid">
              <TextInput
                label="Full Name"
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Tejas Shah"
                value={fullName}
              />
              <div className="if-inline-field">
                <TextInput
                  label="Mobile Number"
                  onChange={(event) => setMobileNumber(event.target.value)}
                  placeholder="7778889997"
                  value={mobileNumber}
                />
                <Button
                  className="if-inline-action"
                  loading={isSendingOtp}
                  onClick={() => onSendOtp(mobileNumber)}
                >
                  Send OTP
                </Button>
              </div>
              {otpRequested ? (
                <div className="if-form-grid-span">
                  <div className="if-field">
                    <OTPInput label="Enter OTP" onChange={setOtpCode} value={otpCode} />
                    {otpError ? <span className="if-error-text">{otpError}</span> : null}
                  </div>
                </div>
              ) : null}
              <TextInput
                label="Date of Birth"
                onChange={(event) => setDateOfBirth(event.target.value)}
                placeholder="YYYY-MM-DD"
                value={dateOfBirth}
              />
              <RadioPillGroup
                label="Gender"
                onChange={(value) => setGender(value as "MALE" | "FEMALE" | "OTHER")}
                options={[
                  { label: "Male", value: "MALE" },
                  { label: "Female", value: "FEMALE" },
                  { label: "Other", value: "OTHER" },
                ]}
                value={gender}
              />
              <TextInput
                label="Email (Optional)"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="name@example.com"
                value={email}
              />
            </div>
          </div>
        ) : null}

        {step === 1 ? (
          <div className="if-screen-section">
            <div className="if-form-grid">
              <TextInput label="Insurance Type" placeholder={displayInsuranceType} readOnly value={displayInsuranceType} />
              <SelectField
                label="Coverage Amount"
                onChange={(event) => setCoverageAmount(event.target.value)}
                options={coverageOptions}
                value={coverageAmount}
              />
              <SelectField
                label="Tenure"
                onChange={(event) => setTenureYears(event.target.value)}
                options={tenureOptions}
                value={tenureYears}
              />

              {insuranceType === "HEALTH" ? (
                <div className="if-form-grid-span">
                  <div className="if-field">
                    <span className="if-group-label">Pre-existing Conditions</span>
                    <div className="if-check-grid">
                      {["Diabetes", "Hypertension", "Asthma", "Cardiac History"].map((condition) => (
                        <label className="if-check-card" key={condition}>
                          <input
                            checked={conditions.includes(condition)}
                            onChange={() => toggleCondition(condition)}
                            type="checkbox"
                          />
                          <span>{condition}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="if-screen-section">
            <div className="if-form-grid">
              <TextInput
                label="Nominee Full Name"
                onChange={(event) => setNomineeName(event.target.value)}
                placeholder="Ananya Shah"
                value={nomineeName}
              />
              <SelectField
                label="Relationship"
                onChange={(event) => setNomineeRelationship(event.target.value)}
                options={relationshipOptions}
                value={nomineeRelationship}
              />
              <TextInput
                label="Date of Birth"
                onChange={(event) => setNomineeDob(event.target.value)}
                placeholder="YYYY-MM-DD"
                value={nomineeDob}
              />
              <TextInput
                label="Mobile Number"
                onChange={(event) => setNomineeMobile(event.target.value)}
                placeholder="8887776665"
                value={nomineeMobile}
              />
            </div>
          </div>
        ) : null}

        <footer className="if-form-footer">
          <Button
            onClick={() => (step === 0 ? onBackToLanding() : setStep((current) => current - 1))}
            variant="ghost"
          >
            Back
          </Button>
          <Button
            loading={step === 0 ? isVerifyingOtp : isSubmitting}
            onClick={() => {
              void handleNext();
            }}
          >
            {step === 2 ? "Submit" : "Next"}
          </Button>
        </footer>
      </section>
    </div>
  );
}
