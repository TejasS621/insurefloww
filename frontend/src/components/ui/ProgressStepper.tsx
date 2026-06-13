import { Check } from "lucide-react";

interface ProgressStep {
  title: string;
}

interface ProgressStepperProps {
  steps: ProgressStep[];
  currentStep: number;
}

/**
 * ProgressStepper communicates the current stage of a multi-step journey.
 * It uses completed, active, and upcoming states defined by the platform tokens.
 */
export function ProgressStepper({ steps, currentStep }: ProgressStepperProps) {
  return (
    <div className="if-stepper" aria-label="Application progress">
      {steps.map((step, index) => {
        const isCompleted = index < currentStep;
        const isActive = index === currentStep;

        return (
          <div className="if-stepper-item" key={step.title}>
            <div
              className={[
                "if-stepper-dot",
                isCompleted ? "is-completed" : "",
                isActive ? "is-active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {isCompleted ? <Check size={14} /> : index + 1}
            </div>
            <div className="if-stepper-copy">
              <span className="if-stepper-label">{step.title}</span>
            </div>
            {index < steps.length - 1 ? <div className="if-stepper-line" /> : null}
          </div>
        );
      })}
    </div>
  );
}
