import { useState } from "react";

export function usePendingAction<T extends string = string>() {
  const [pending, setPending] = useState<T | null>(null);

  const run = async (action: T, fn: () => Promise<void>) => {
    if (pending !== null) return;
    setPending(action);
    try {
      await fn();
    } finally {
      setPending(null);
    }
  };

  return { pending, run };
}
