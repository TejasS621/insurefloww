import { Minus, Plus } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { ProgressStepper } from "../../components/ui/ProgressStepper";
import { RadioPillGroup } from "../../components/ui/RadioPillGroup";
import { SelectField } from "../../components/ui/SelectField";
import { TextInput } from "../../components/ui/TextInput";
import type { ApplicationSummary, CustomerApplicationPayload } from "../../services/api/customer";

type InsuranceType = "HEALTH" | "LIFE" | "VEHICLE" | "TRAVEL" | "HOME";

interface ApplicationFlowScreenProps {
  insuranceType: InsuranceType;
  formError?: string;
  fieldErrors?: Record<string, string>;
  initialMobileNumber?: string;
  isSubmitting: boolean;
  onBackToLanding: () => void;
  onSubmit: (payload: CustomerApplicationPayload) => Promise<void>;
  resumedApplication: ApplicationSummary | null;
}

const coverageOptions = [
  { label: "Rs 5L", value: "500000" },
  { label: "Rs 10L", value: "1000000" },
  { label: "Rs 25L", value: "2500000" },
  { label: "Rs 50L", value: "5000000" },
  { label: "Rs 1Cr", value: "10000000" },
];

const tenureOptions = [
  { label: "1 year", value: "1" },
  { label: "2 years", value: "2" },
  { label: "3 years", value: "3" },
];

const stepItems = [{ title: "Personal Details" }, { title: "Coverage Details" }];

const healthMembersList = ["Self", "Spouse", "Son", "Daughter", "Father", "Mother"];
const defaultConditionOptions = ["Diabetes", "Hypertension", "Asthma", "Cardiac History"];

/**
 * ApplicationFlowScreen collects only the insured person's details and coverage selections.
 * Authentication is handled earlier in the customer login screen so this form stays focused on the application itself.
 */
export function ApplicationFlowScreen({
  insuranceType,
  formError,
  fieldErrors = {},
  initialMobileNumber = "",
  isSubmitting,
  onBackToLanding,
  onSubmit,
  resumedApplication,
}: ApplicationFlowScreenProps) {
  const [step, setStep] = useState(0);
  const [fullName, setFullName] = useState("");
  const [mobileNumber, setMobileNumber] = useState(initialMobileNumber);
  const [email, setEmail] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [gender, setGender] = useState<"MALE" | "FEMALE" | "OTHER">("MALE");
  const [coverageAmount, setCoverageAmount] = useState("1000000");
  const [tenureYears, setTenureYears] = useState("1");
  const [insuredMembers, setInsuredMembers] = useState<string[]>(["Self"]);
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [isSmoker, setIsSmoker] = useState<"YES" | "NO">("NO");
  const [conditions, setConditions] = useState<string[]>([]);
  const [otherCondition, setOtherCondition] = useState("");
  const [vehicleType, setVehicleType] = useState<"CAR" | "BIKE">("CAR");
  const [regNumber, setRegNumber] = useState("");
  const [mfgYear, setMfgYear] = useState("");
  const [fuelType, setFuelType] = useState<"PETROL" | "DIESEL" | "EV" | "CNG">("PETROL");
  const [destination, setDestination] = useState("");
  const [travelStartDate, setTravelStartDate] = useState("");
  const [travelEndDate, setTravelEndDate] = useState("");
  const [numTravellers, setNumTravellers] = useState("");
  const [lifeSumInsured, setLifeSumInsured] = useState(10000000);

  const displayInsuranceType = useMemo(
    () => insuranceType.charAt(0) + insuranceType.slice(1).toLowerCase(),
    [insuranceType],
  );

  const calculatedBmi = useMemo(() => {
    const parsedHeight = Number(heightCm);
    const parsedWeight = Number(weightKg);

    if (!parsedHeight || !parsedWeight || parsedHeight <= 0 || parsedWeight <= 0) {
      return null;
    }

    return (parsedWeight / ((parsedHeight / 100) ** 2)).toFixed(2);
  }, [heightCm, weightKg]);

  const toggleCondition = (condition: string) => {
    setConditions((current) =>
      current.includes(condition)
        ? current.filter((item) => item !== condition)
        : [...current, condition],
    );
  };

  const toggleInsuredMember = (member: string) => {
    setInsuredMembers((current) =>
      current.includes(member)
        ? current.filter((item) => item !== member)
        : [...current, member],
    );
  };

  const handleNext = async () => {
    if (step === 1) {
      await onSubmit({
        insuranceType,
        fullName,
        mobileNumber,
        email,
        dateOfBirth,
        gender,
        coverageAmount: insuranceType === "LIFE" ? lifeSumInsured : Number(coverageAmount),
        tenureYears: Number(tenureYears),
        guestIdentifier: `guest-${mobileNumber}`,
        healthConditions:
          insuranceType === "HEALTH"
            ? [...conditions, ...(otherCondition.trim() ? [otherCondition.trim()] : [])]
            : [],
        smoker: insuranceType === "HEALTH" ? isSmoker === "YES" : false,
        insuredMembers: insuranceType === "HEALTH" ? insuredMembers : ["Self"],
        heightCm: insuranceType === "HEALTH" && heightCm ? Number(heightCm) : null,
        weightKg: insuranceType === "HEALTH" && weightKg ? Number(weightKg) : null,
      });
      return;
    }

    setStep(1);
  };

  const formatLifeSumInsuredLabel = (value: number) => {
    if (value >= 10000000) {
      return `Rs ${value / 10000000}Cr`;
    }
    return `Rs ${value / 100000}L`;
  };

  return (
    <div className="if-screen-stack">
      {resumedApplication ? (
        <div className="if-resume-banner">
          <div>
            <strong>Active application found.</strong>
            <span> Continue from your saved quote selection if you want to pick up the same journey.</span>
          </div>
          <div className="if-resume-actions">
            <Button onClick={() => setStep(1)}>Resume</Button>
            <Button onClick={onBackToLanding} variant="ghost">
              Start New
            </Button>
          </div>
        </div>
      ) : null}

      {formError ? <ErrorCard message={formError} /> : null}

      <div style={{ margin: "0 auto", maxWidth: "720px", width: "100%" }}>
        <section className="if-surface-card" style={{ padding: "40px 48px" }}>
          <ProgressStepper currentStep={step} steps={stepItems} />

          {step === 0 ? (
            <div className="if-screen-section">
              <div className="if-form-grid" style={{ gridTemplateColumns: "1fr" }}>
                <TextInput
                  error={
                    fieldErrors.fullName ||
                    fieldErrors.first_name ||
                    fieldErrors.last_name ||
                    fieldErrors["personal_details.first_name"] ||
                    fieldErrors["personal_details.last_name"]
                  }
                  label="Full Name"
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="e.g. Tejas Sahare"
                  value={fullName}
                />
                <TextInput
                  error={
                    fieldErrors.mobileNumber ||
                    fieldErrors.mobile_number ||
                    fieldErrors["personal_details.mobile_number"]
                  }
                  label="Mobile Number"
                  onChange={(event) => setMobileNumber(event.target.value)}
                  placeholder="e.g. 7778889997"
                  value={mobileNumber}
                />
                <div style={{ display: "grid", gap: "16px", gridTemplateColumns: "1fr 1fr" }}>
                  <TextInput
                    error={
                      fieldErrors.dateOfBirth ||
                      fieldErrors.date_of_birth ||
                      fieldErrors["personal_details.date_of_birth"]
                    }
                    helperText="Use DD/MM/YYYY or YYYY-MM-DD"
                    label="Date of Birth"
                    onChange={(event) => setDateOfBirth(event.target.value)}
                    placeholder="e.g. 02/11/1999"
                    type="text"
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
                </div>
                <TextInput
                  error={fieldErrors.email || fieldErrors["personal_details.email"]}
                  label="Email (Optional)"
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="e.g. name@example.com"
                  type="email"
                  value={email}
                />
              </div>
            </div>
          ) : null}

          {step === 1 ? (
            <div className="if-screen-section">
              <div className="if-form-grid" style={{ gridTemplateColumns: "1fr" }}>
                <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
                  <span className="if-group-label">Insurance Type</span>
                  <span className="if-badge if-badge-admin" style={{ fontSize: "13px", padding: "6px 14px" }}>
                    {displayInsuranceType}
                  </span>
                </div>

                {insuranceType !== "LIFE" ? (
                  <div style={{ display: "grid", gap: "16px", gridTemplateColumns: "1fr 1fr" }}>
                    <SelectField
                      error={
                        fieldErrors.coverageAmount ||
                        fieldErrors.coverage_amount ||
                        fieldErrors["coverage_details.coverage_amount"]
                      }
                      label="Coverage Amount"
                      onChange={(event) => setCoverageAmount(event.target.value)}
                      options={coverageOptions}
                      value={coverageAmount}
                    />
                    <SelectField
                      error={
                        fieldErrors.tenureYears ||
                        fieldErrors.tenure_years ||
                        fieldErrors["coverage_details.tenure_years"]
                      }
                      label="Tenure"
                      onChange={(event) => setTenureYears(event.target.value)}
                      options={tenureOptions}
                      value={tenureYears}
                    />
                  </div>
                ) : null}

                {insuranceType === "HEALTH" ? (
                  <>
                    <div style={{ display: "grid", gap: "16px", gridTemplateColumns: "1fr 1fr" }}>
                      <TextInput
                        error={
                          fieldErrors.heightCm ||
                          fieldErrors.height_cm ||
                          fieldErrors["health_details.height_cm"]
                        }
                        helperText={calculatedBmi ? `BMI: ${calculatedBmi}` : "Enter height in centimeters"}
                        label="Height (cm)"
                        min="0"
                        onChange={(event) => setHeightCm(event.target.value)}
                        placeholder="e.g. 175"
                        type="number"
                        value={heightCm}
                      />
                      <TextInput
                        error={
                          fieldErrors.weightKg ||
                          fieldErrors.weight_kg ||
                          fieldErrors["health_details.weight_kg"]
                        }
                        helperText="Enter weight in kilograms"
                        label="Weight (kg)"
                        min="0"
                        onChange={(event) => setWeightKg(event.target.value)}
                        placeholder="e.g. 72"
                        type="number"
                        value={weightKg}
                      />
                    </div>

                    <RadioPillGroup
                      label="Smoker"
                      onChange={(value) => setIsSmoker(value as "YES" | "NO")}
                      options={[
                        { label: "No", value: "NO" },
                        { label: "Yes", value: "YES" },
                      ]}
                      value={isSmoker}
                    />

                    <div className="if-field">
                      <span className="if-group-label">Insured Members</span>
                      <div className="if-chip-row" style={{ marginTop: "8px" }}>
                        {healthMembersList.map((member) => {
                          const isActive = insuredMembers.includes(member);
                          return (
                            <span
                              key={member}
                              className={`if-chip ${isActive ? "is-active" : ""}`}
                              onClick={() => toggleInsuredMember(member)}
                            >
                              {isActive ? <Minus size={12} /> : <Plus size={12} />}
                              {member}
                            </span>
                          );
                        })}
                      </div>
                    </div>

                    <div className="if-field" style={{ marginTop: "8px" }}>
                      <span className="if-group-label">Pre-existing Medical Conditions</span>
                      <div className="if-check-grid" style={{ marginTop: "8px" }}>
                        {defaultConditionOptions.map((condition) => (
                          <label className="if-check-card" key={condition} style={{ cursor: "pointer" }}>
                            <input
                              checked={conditions.includes(condition)}
                              onChange={() => toggleCondition(condition)}
                              type="checkbox"
                            />
                            <span style={{ marginLeft: "8px" }}>{condition}</span>
                          </label>
                        ))}
                      </div>
                      <TextInput
                        label="Other Condition"
                        onChange={(event) => setOtherCondition(event.target.value)}
                        placeholder="Specify any other condition"
                        value={otherCondition}
                      />
                    </div>
                  </>
                ) : null}

                {insuranceType === "VEHICLE" ? (
                  <div style={{ display: "grid", gap: "16px" }}>
                    <div style={{ display: "grid", gap: "16px", gridTemplateColumns: "1fr 1fr" }}>
                      <RadioPillGroup
                        label="Vehicle Type"
                        onChange={(value) => setVehicleType(value as "CAR" | "BIKE")}
                        options={[
                          { label: "Car", value: "CAR" },
                          { label: "Bike", value: "BIKE" },
                        ]}
                        value={vehicleType}
                      />
                      <TextInput
                        label="Registration Number"
                        onChange={(event) => setRegNumber(event.target.value)}
                        placeholder="e.g. MH12AB1234"
                        value={regNumber}
                      />
                    </div>
                    <div style={{ display: "grid", gap: "16px", gridTemplateColumns: "1fr 1fr" }}>
                      <TextInput
                        label="Manufacturing Year"
                        onChange={(event) => setMfgYear(event.target.value)}
                        placeholder="e.g. 2024"
                        type="number"
                        value={mfgYear}
                      />
                      <RadioPillGroup
                        label="Fuel Type"
                        onChange={(value) => setFuelType(value as "PETROL" | "DIESEL" | "EV" | "CNG")}
                        options={[
                          { label: "Petrol", value: "PETROL" },
                          { label: "Diesel", value: "DIESEL" },
                          { label: "EV", value: "EV" },
                          { label: "CNG", value: "CNG" },
                        ]}
                        value={fuelType}
                      />
                    </div>
                  </div>
                ) : null}

                {insuranceType === "TRAVEL" ? (
                  <div style={{ display: "grid", gap: "16px" }}>
                    <TextInput
                      label="Destination"
                      onChange={(event) => setDestination(event.target.value)}
                      placeholder="e.g. Schengen Area"
                      value={destination}
                    />
                    <div style={{ display: "grid", gap: "16px", gridTemplateColumns: "1fr 1fr" }}>
                      <TextInput
                        label="Travel Start Date"
                        onChange={(event) => setTravelStartDate(event.target.value)}
                        type="date"
                        value={travelStartDate}
                      />
                      <TextInput
                        label="Travel End Date"
                        onChange={(event) => setTravelEndDate(event.target.value)}
                        type="date"
                        value={travelEndDate}
                      />
                    </div>
                    <TextInput
                      label="Number of Travellers"
                      onChange={(event) => setNumTravellers(event.target.value)}
                      placeholder="e.g. 1"
                      type="number"
                      value={numTravellers}
                    />
                  </div>
                ) : null}

                {insuranceType === "LIFE" ? (
                  <div style={{ display: "grid", gap: "20px" }}>
                    <div className="if-field">
                      <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
                        <span className="if-group-label">Sum Insured</span>
                        <span style={{ fontWeight: 700 }}>{formatLifeSumInsuredLabel(lifeSumInsured)}</span>
                      </div>
                      <input
                        type="range"
                        min={1000000}
                        max={100000000}
                        step={1000000}
                        value={lifeSumInsured}
                        onChange={(event) => setLifeSumInsured(Number(event.target.value))}
                        style={{ cursor: "pointer", marginTop: "12px", width: "100%" }}
                      />
                    </div>
                    <SelectField
                      error={
                        fieldErrors.tenureYears ||
                        fieldErrors.tenure_years ||
                        fieldErrors["coverage_details.tenure_years"]
                      }
                      label="Tenure"
                      onChange={(event) => setTenureYears(event.target.value)}
                      options={tenureOptions}
                      value={tenureYears}
                    />
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}

          <footer
            className="if-form-footer"
            style={{ borderTop: "1px solid var(--if-border)", marginTop: "32px", paddingTop: "24px" }}
          >
            <Button
              onClick={() => (step === 0 ? onBackToLanding() : setStep(0))}
              variant="ghost"
            >
              Back
            </Button>
            <Button loading={isSubmitting} onClick={() => void handleNext()}>
              {step === 1 ? "Get Quotes" : "Next"}
            </Button>
          </footer>
        </section>
      </div>
    </div>
  );
}
