import type { Problem } from "../../api/types";
import { DORM_LABEL, formatDay, formatMoney } from "../../lib/format";

/** One plain sentence per problem the quote check found. */
export function describeProblem(problem: Problem, currency: string): string {
  const where = problem.date && problem.room_type ? `${formatDay(problem.date)}, ${problem.room_type}: ` : "";
  switch (problem.kind) {
    case "missing_rate":
      return `${where}no usable rate (${problem.detail ?? "left blank"}).`;
    case "short_inventory":
      return `${where}we asked for ${problem.rooms_requested} rooms and ${DORM_LABEL} offered ${problem.rooms_offered}.`;
    case "total_mismatch":
      return `${problem.room_type} total: ${DORM_LABEL} wrote ${formatMoney(problem.dorm_total ?? "0", currency)}, but their rates add up to ${formatMoney(problem.computed_total ?? "0", currency)}.`;
    case "below_minimum_rate":
      return `${where}${formatMoney(problem.rate ?? "0", currency)} is below the hotel's minimum of ${formatMoney(problem.minimum_rate ?? "0", currency)}${problem.detail ? ` (policy: "${problem.detail}")` : ""}.`;
    case "unclear_in_reply":
      return problem.detail ?? "Part of the reply is unclear.";
  }
}
