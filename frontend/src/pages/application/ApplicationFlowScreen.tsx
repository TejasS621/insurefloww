import { useState } from "react";

import { Button } from "../../components/ui/Button";
import { OTPInput } from "../../components/ui/OTPInput";
import { ProgressStepper } from "../../components/ui/ProgressStepper";
import { RadioPillGroup } from "../../components/ui/RadioPillGroup";
import { SelectField } from "../../components/ui/SelectField";
import { TextInput } from "../../components/ui/TextInput";

type InsuranceType = "health" | "vehicle" | "travel" | "home" | "life";

interface ApplicationFlowScreenProps {
  insuranceType: InsuranceType;
  onBackToLanding: () => void;
  onSubmit: () => void;
}

const coverageOptions = [
  { label: "₹5L", value: "5L" },
  { label: "₹10L", value: "10L" },
  { label: "₹25L", value: "25L" },
  { label: "₹50L", value: "50L" },
  { label: "₹1Cr", value: "1Cr" },
];

const tenureOptions = [
  { label: "1 year", value: "1" },
  { label: "2 years", value: "2" },
  { label: "3 years", value: "3" },
];

const relationshipOptions = [
  { label: "Spouse", value: "spouse" },
  { label: "Parent", value: "parent" },
  { label: "Sibling", value: "sibling" },
  { label: "Child", value: "child" },
];

const stepItems = [
  { title: "Personal Details" },
  { title: "Coverage Details" },
  { title: "Nominee Details" },
];

/**
 * ApplicationFlowScreen renders the three-step customer application form.
 * It previews journey resume messaging and insurance-specific coverage fields.
 */
export function ApplicationFlowScreen({
  insuranceType,
  onBackToLanding,
  onSubmit,
}: ApplicationFlowScreenProps) {
  const [step, setStep] = useState(0);
  const [gender, setGender] = useState("male");
  const [members, setMembers] = useState(["Self", "Spouse", "Child"]);
  const [conditions, setConditions] = useState(["Diabetes"]);

  const addMember = () => {
    const pool = ["Parent", "Child", "Spouse", "Sibling"];
    const next = pool.find((member) => !members.includes(member));
    if (next) {
      setMembers((current) => [...current, next]);
    }
  };

  const toggleCondition = (condition: string) => {
    setConditions((current) =>
      current.includes(condition)
        ? current.filter((item) => item !== condition)
        : [...current, condition],
    );
  };

  return (
    <div className="if-screen-stack">
      <div className="if-resume-banner">
        <div>
          <strong>You have an active application. Continue where you left off.</strong>
        </div>
        <div className="if-resume-actions">
          <Button>Resume</Button>
          <Button onClick={onBackToLanding} variant="ghost">
            Start New
          </Button>
        </div>
      </div>

      <section className="if-surface-card">
        <ProgressStepper currentStep={step} steps={stepItems} />

        {step === 0 ? (
          <div className="if-screen-section">
            <div className="if-form-grid">
              <TextInput id="full-name" label="Full Name" placeholder="Tejas Shah" />
              <div className="if-inline-field">
                <TextInput id="mobile-number" label="Mobile Number" placeholder="7778889997" />
                <Button className="if-inline-action">Send OTP</Button>
              </div>
              <div className="if-form-grid-span">
                <OTPInput label="Enter OTP" />
              </div>
              <TextInput id="dob" label="Date of Birth" placeholder="DD/MM/YYYY" />
              <RadioPillGroup
                label="Gender"
                onChange={setGender}
                options={[
                  { label: "Male", value: "male" },
                  { label: "Female", value: "female" },
                  { label: "Other", value: "other" },
                ]}
                value={gender}
              />
              <TextInput id="email" label="Email (Optional)" placeholder="name@example.com" />
            </div>
          </div>
        ) : null}

        {step === 1 ? (
          <div className="if-screen-section">
            <div className="if-form-grid">
              <TextInput
                id="insurance-type"
                label="Insurance Type"
                placeholder={insuranceType.charAt(0).toUpperCase() + insuranceType.slice(1)}
                readOnly
              />
              <SelectField label="Coverage Amount" options={coverageOptions} />
              <SelectField label="Tenure" options={tenureOptions} />

              {insuranceType === "health" ? (
                <>
                  <div className="if-form-grid-span">
                    <div className="if-field">
                      <span className="if-group-label">Insured Members</span>
                      <div className="if-chip-row">
                        {members.map((member) => (
                          <span className="if-chip" key={member}>
                            {member}
                          </span>
                        ))}
                        <button className="if-chip if-chip-action" onClick={addMember} type="button">
                          + Add Member
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="if-form-grid-span">
                    <div className="if-field">
                      <span className="if-group-label">Pre-existing Conditions</span>
                      <div className="if-check-grid">
                        {["Diabetes", "Hypertension", "Asthma", "Cardiac History"].map(
                          (condition) => (
                            <label className="if-check-card" key={condition}>
                              <input
                                checked={conditions.includes(condition)}
                                onChange={() => toggleCondition(condition)}
                                type="checkbox"
                              />
                              <span>{condition}</span>
                            </label>
                          ),
                        )}
                      </div>
                    </div>
                  </div>
                </>
              ) : null}

              {insuranceType === "vehicle" ? (
                <>
                  <SelectField
                    label="Vehicle Type"
                    options={[
                      { label: "Car", value: "car" },
                      { label: "Bike", value: "bike" },
                      { label: "SUV", value: "suv" },
                    ]}
                  />
                  <TextInput label="Registration Number" mono placeholder="MH12AB1234" />
                  <TextInput label="Manufacturing Year" placeholder="2023" />
                  <SelectField
                    label="Fuel Type"
                    options={[
                      { label: "Petrol", value: "petrol" },
                      { label: "Diesel", value: "diesel" },
                      { label: "Electric", value: "electric" },
                    ]}
                  />
                </>
              ) : null}

              {insuranceType === "travel" ? (
                <>
                  <TextInput label="Destination" placeholder="Singapore" />
                  <TextInput label="Travel Dates" placeholder="15 Aug 2026 - 24 Aug 2026" />
                  <TextInput label="Number of Travellers" placeholder="3" />
                </>
              ) : null}

              {insuranceType === "life" ? (
                <TextInput label="Sum Insured" placeholder="₹1,00,00,000" mono />
              ) : null}

              {insuranceType === "home" ? (
                <>
                  <TextInput label="Property Address" placeholder="Apartment or house address" />
                  <SelectField
                    label="Property Type"
                    options={[
                      { label: "Apartment", value: "apartment" },
                      { label: "Independent House", value: "house" },
                      { label: "Villa", value: "villa" },
                    ]}
                  />
                  <TextInput label="Built-up Area" placeholder="1800 sq ft" />
                </>
              ) : null}
            </div>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="if-screen-section">
            <div className="if-form-grid">
              <TextInput label="Nominee Full Name" placeholder="Ananya Shah" />
              <SelectField label="Relationship" options={relationshipOptions} />
              <TextInput label="Date of Birth" placeholder="DD/MM/YYYY" />
              <TextInput label="Mobile Number" placeholder="8887776665" />
            </div>
            {insuranceType === "life" ? (
              <div className="if-inline-note">
                Life insurance nominee details will be pre-filled into the proposal summary.
              </div>
            ) : null}
          </div>
        ) : null}

        <footer className="if-form-footer">
          <Button onClick={() => (step === 0 ? onBackToLanding() : setStep((current) => current - 1))} variant="ghost">
            Back
          </Button>
          <Button onClick={() => (step === 2 ? onSubmit() : setStep((current) => current + 1))}>
            {step === 2 ? "Submit" : "Next"}
          </Button>
        </footer>
      </section>
    </div>
  );
}
