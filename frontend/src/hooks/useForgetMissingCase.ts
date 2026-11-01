import { useEffect } from "react";

import { ApiError } from "../api/http";

const NOT_FOUND = 404;

/** A case in the address bar may no longer exist (for example after the data was cleared): drop it and show the inbox. */
export function useForgetMissingCase(error: Error | null, forget: () => void) {
  useEffect(() => {
    if (error instanceof ApiError && error.status === NOT_FOUND) forget();
  }, [error, forget]);
}
