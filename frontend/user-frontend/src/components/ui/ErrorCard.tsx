import { Button } from "./Button";

interface ErrorCardProps {
  message: string;
  onRetry?: () => void;
}

/**
 * ErrorCard renders a safe retry-oriented failure state without leaking raw errors.
 * Data sections use it for recoverable API failures and retry flows.
 */
export function ErrorCard({ message, onRetry }: ErrorCardProps) {
  return (
    <div className="if-error-card">
      <h3>Something went wrong</h3>
      <p>{message}</p>
      {onRetry ? (
        <div className="if-error-card-action">
          <Button onClick={onRetry}>Retry</Button>
        </div>
      ) : null}
    </div>
  );
}
