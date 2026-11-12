import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { useSession } from "../auth";

export type AliasState =
  | { status: "loading" }
  | { status: "verified"; address: string; token: string }
  | { status: "unverified"; message: string }
  | { status: "unconfigured"; message: string }
  | { status: "error"; message: string };

export function useForwardingAlias() {
  const { user } = useSession();
  const [state, setState] = useState<AliasState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    api.alias()
      .then((data) => {
        if (active) {
          setState({ status: "verified", address: data.address, token: data.token });
        }
      })
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError) {
          if (err.status === 403) {
            setState({ status: "unverified", message: err.message });
          } else if (err.status === 503) {
            setState({ status: "unconfigured", message: err.message });
          } else {
            setState({ status: "error", message: err.message });
          }
        } else {
          setState({ status: "error", message: (err as Error).message });
        }
      });
    return () => {
      active = false;
    };
  }, [user]);

  return state;
}
