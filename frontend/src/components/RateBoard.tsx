import type { Night, Quote } from "../api/types";
import { formatDay, formatMoney, sortRoomTypes } from "../lib/format";

interface Props {
  nights: Night[];
  quote?: Quote | null;
}

/** The grid at the heart of the job: rooms needed per night and type, then the rate the DORM gave for each cell. */
export function RateBoard({ nights, quote = null }: Props) {
  const roomTypes = sortRoomTypes(nights.flatMap((night) => Object.keys(night.rooms)));
  const currency = quote?.currency ?? "EUR";

  return (
    <div className="board-scroll">
      <table className="board">
        <thead>
          <tr>
            <th scope="col">Night</th>
            {roomTypes.map((type) => (
              <th scope="col" key={type}>
                {type}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {nights.map((night) => (
            <tr key={night.date}>
              <th scope="row">{formatDay(night.date)}</th>
              {roomTypes.map((type) => (
                <BoardCell key={type} night={night} roomType={type} quote={quote} currency={currency} />
              ))}
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">{quote ? "Revenue" : "Room nights"}</th>
            {roomTypes.map((type) => (
              <td key={type} className="board__total">
                {totalFor(type, nights, quote, currency)}
              </td>
            ))}
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

function totalFor(type: string, nights: Night[], quote: Quote | null, currency: string): string {
  if (!quote) return String(nights.reduce((sum, night) => sum + (night.rooms[type] ?? 0), 0));
  const total = quote.totals_by_type.find((item) => item.room_type === type);
  return total ? formatMoney(total.revenue, currency) : "None quoted";
}

interface CellProps {
  night: Night;
  roomType: string;
  quote: Quote | null;
  currency: string;
}

function BoardCell({ night, roomType, quote, currency }: CellProps) {
  const needed = night.rooms[roomType] ?? 0;
  if (needed === 0) return <td className="board__cell board__cell--empty">–</td>;
  if (!quote) return <td className="board__cell"><strong>{needed}</strong><span>rooms</span></td>;

  const line = quote.lines.find((item) => item.date === night.date && item.room_type === roomType);
  const problem = quote.problems.find((item) => item.date === night.date && item.room_type === roomType);
  if (!line) {
    return <td className="board__cell board__cell--warn"><strong>No rate</strong><span>{needed} rooms</span></td>;
  }
  const short = problem?.kind === "short_inventory";
  return (
    <td className={`board__cell ${short ? "board__cell--warn" : "board__cell--ok"}`}>
      <strong>{formatMoney(line.rate, currency)}</strong>
      <span>{short ? `${line.rooms} of ${needed} rooms` : `${needed} rooms`}</span>
    </td>
  );
}
