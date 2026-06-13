import { useState } from "react";

/**
 * useAsyncAction centralizes async button loading and double-submit prevention.
 * Screens wrap form submits and mutations with it to keep buttons single-fire.
 */
export function useAsyncAction() {
  const [isLoading, setIsLoading] = useState(false);

  const run = async <T>(action: () => Promise<T>): Promise<T> => {
    setIsLoading(true);
    try {
      return await action();
    } finally {
      setIsLoading(false);
    }
  };

  return { isLoading, run };
}
