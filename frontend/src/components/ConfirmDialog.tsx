import { createContext, useCallback, useContext, useRef, useState } from "react";
import type { ReactNode } from "react";

type Options = { title: string; body: string; confirmLabel?: string; tone?: "danger" | "default" };
type ConfirmApi = { ask: (options: Options) => Promise<boolean> };
const ConfirmContext = createContext<ConfirmApi | null>(null);

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [options, setOptions] = useState<Options | null>(null);
  const resolver = useRef<((value: boolean) => void) | null>(null);

  const ask = useCallback((next: Options) => {
    setOptions(next);
    return new Promise<boolean>((resolve) => { resolver.current = resolve; });
  }, []);

  const answer = (value: boolean) => {
    resolver.current?.(value);
    resolver.current = null;
    setOptions(null);
  };

  return (
    <ConfirmContext.Provider value={{ ask }}>
      {children}
      {options && (
        <div className="dialog-backdrop">
          <div className="dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title">
            <h2 id="confirm-title">{options.title}</h2>
            <p>{options.body}</p>
            <div className="dialog-actions">
              <button type="button" className="btn" onClick={() => answer(false)}>Cancel</button>
              <button
                type="button"
                className={options.tone === "danger" ? "btn btn-danger" : "btn btn-accent"}
                onClick={() => answer(true)}
              >
                {options.confirmLabel ?? "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const context = useContext(ConfirmContext);
  if (!context) throw new Error("useConfirm must be used inside ConfirmProvider");
  return context;
}
