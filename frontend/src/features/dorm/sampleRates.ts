/** One-click sample answers, so a demo does not need typing. They fill the grid the way the DORM would. */

export interface RateSample {
  label: string;
  /** Rate per night, in order, for each room type. null leaves the cell empty. */
  rates: Record<string, (number | string | null)[]>;
  note: string;
  /** Where a correction says "(you offered 6)", answer that all requested rooms are available. */
  confirmsFullInventory: boolean;
}

export const RATE_SAMPLES: RateSample[] = [
  {
    label: "Clean reply",
    rates: {
      "Standard King": [189, 209, 179],
      "Deluxe King": [229, 249, 219],
      "Junior Suite": [null, 360, null],
    },
    note: [
      "Hi Umar,",
      "Happy to help, rates are filled in below, in EUR.",
      "Rates are exclusive of VAT (6%) and city tax (EUR 4 per person per night). Commission 10% on room revenue. Option until 15 Jan 2027.",
      "Breakfast: EUR 22 per person per day, buffet.",
      "Welcome reception: Atlantic Room, from EUR 48 per person with 2 drinks. Room hire waived above EUR 2,500 F&B.",
      "Attrition: 10% allowed until 30 days prior, no penalty.",
      "All the rooms you asked for are available.",
    ].join("\n"),
    confirmsFullInventory: true,
  },
  {
    label: "Messy reply",
    rates: {
      "Standard King": [129, 209, 179],
      "Deluxe King": [0, 249, 219],
      "Junior Suite": [null, "TBC", null],
    },
    note: [
      "Umar, see the grid. Sunday we are tight: I can give you only 6 Deluxe Kings.",
      "Junior suite TBC, I need to check with the front office.",
      "Rates net, taxes on top. Commission 8%.",
    ].join("\n"),
    confirmsFullInventory: false,
  },
];

const NOTE_ATTRIBUTE = "data-sample-note";
const RATE_CELL_CLASS = "rate";

interface RateCell {
  roomType: string;
  night: number;
  cell: HTMLTableCellElement;
}

/**
 * The cells a DORM prices: under each "<room type> Rate" column, one per night, except nights where the
 * rooms column says 0. Found from the grid's own headers, so any grid we sent can be answered.
 */
function findRateCells(doc: Document): RateCell[] {
  const rows = [...doc.querySelectorAll("table tr")];
  if (rows.length === 0) return [];
  const headers = [...rows[0].querySelectorAll("th")].map((header) => header.textContent ?? "");
  const nights = rows.slice(1).filter((row) => !row.textContent?.startsWith("Total"));
  return headers.flatMap((header, column) => {
    if (!header.includes("Rate")) return [];
    const roomType = header.replace(/\s*Rate.*$/s, "").trim(); // A <br> in the header leaves no space before "Rate".
    return nights.flatMap((row, night) => {
      const cells = row.querySelectorAll("td"); // Body rows start with the date cell, so cell n sits under header n.
      const needed = cells[column - 1]?.textContent?.trim() !== "0"; // The rooms cell just before the rate cell.
      const cell = cells[column];
      return cell && needed ? [{ roomType, night, cell }] : [];
    });
  });
}

/** The cells to fill in: the ones the server marked, or for an older email without marks, every rate cell. */
function cellsToFill(doc: Document): RateCell[] {
  const all = findRateCells(doc);
  const marked = all.filter(({ cell }) => cell.classList.contains(RATE_CELL_CLASS));
  return doc.querySelector(`td.${RATE_CELL_CLASS}`) ? marked : all;
}

/** Highlight the cells to fill in. */
export function markRateCells(doc: Document): void {
  cellsToFill(doc).forEach(({ cell }) => cell.classList.add(RATE_CELL_CLASS));
}

/** Type the sample rates into the grid and put the note above the quoted email. */
export function applySampleRates(doc: Document, sample: RateSample): void {
  cellsToFill(doc).forEach(({ roomType, night, cell }) => {
    const value = sample.rates[roomType]?.[night];
    if (value !== null && value !== undefined) cell.textContent = String(value);
  });
  if (sample.confirmsFullInventory) confirmOfferedRooms(doc);
  writeNote(doc, sample.note);
}

/** "10 (you offered 6)" becomes "10": the DORM agrees to release every room asked for. */
function confirmOfferedRooms(doc: Document): void {
  doc.querySelectorAll("table td").forEach((cell) => {
    const asked = cell.textContent?.match(/^(\d+) \(you offered \d+\)/)?.[1];
    if (asked) cell.textContent = asked;
  });
}

function writeNote(doc: Document, note: string): void {
  doc.querySelector(`[${NOTE_ATTRIBUTE}]`)?.remove();
  const paragraph = doc.createElement("p");
  paragraph.setAttribute(NOTE_ATTRIBUTE, "");
  note.split("\n").forEach((line, index) => {
    if (index > 0) paragraph.appendChild(doc.createElement("br"));
    paragraph.appendChild(doc.createTextNode(line));
  });
  doc.body.prepend(paragraph);
}
