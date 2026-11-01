import { useRef } from "react";

import { EMAIL_STYLES } from "../../components/EmailPreview";
import { Notice } from "../../components/Notice";
import { applySampleRates, markRateCells, RATE_SAMPLES } from "./sampleRates";

/** Rate cells stand out so it is obvious where to type. */
const EDITOR_STYLES = "td.rate{min-width:5.5rem;outline:1px dashed #c9a400}hr{border:0;border-top:1px solid #cfd6dd}";

interface Props {
  to: string;
  subject: string;
  /** The email being answered, with its grid. */
  quotedHtml: string;
  quotedFrom: string;
  busy: boolean;
  error: string | null;
  onSend: (html: string) => void;
  onCancel: () => void;
}

/**
 * "Reply all" the way a mail client does it: the email you received opens as an editable copy, and you type
 * your rates straight into its grid. What you send is that edited HTML.
 */
export function ReplyEditor({ to, subject, quotedHtml, quotedFrom, busy, error, onSend, onCancel }: Props) {
  const frame = useRef<HTMLIFrameElement>(null);
  const editedDocument = () => frame.current?.contentDocument ?? null;

  const fitToContent = () => {
    const body = editedDocument()?.body;
    if (frame.current && body) frame.current.style.height = `${Math.max(body.scrollHeight + 24, 320)}px`;
  };

  const prepare = () => {
    const doc = editedDocument();
    if (!doc) return;
    markRateCells(doc);
    doc.addEventListener("input", fitToContent);
    doc.addEventListener("keydown", (event) => moveToNextRateCell(doc, event));
    fitToContent();
  };

  const fillWithSample = (index: number) => {
    const doc = editedDocument();
    if (doc) applySampleRates(doc, RATE_SAMPLES[index]);
    fitToContent();
  };

  const document_ = `<!doctype html><html><head><style>${EMAIL_STYLES}${EDITOR_STYLES}</style></head><body contenteditable="true"><p><br></p><p style="color:#5c5c5c">${quotedFrom} wrote:</p><hr>${quotedHtml}</body></html>`;

  return (
    <section className="card" id="reply-editor">
      <header className="card__header">
        <h3 className="card__title">Reply all</h3>
        <span className="card__meta">Click in a yellow cell and type the rate. Tab moves to the next one.</span>
      </header>
      <div className="card__body">
        <article className="mail">
          <dl className="mail__meta">
            <dt>To</dt>
            <dd>{to}</dd>
            <dt>Subject</dt>
            <dd>RE: {subject}</dd>
          </dl>
          <iframe ref={frame} className="mail__body" title="Your reply" sandbox="allow-same-origin" srcDoc={document_} onLoad={prepare} />
        </article>
        <div className="form__row">
          <span className="muted">Demo shortcut:</span>
          {RATE_SAMPLES.map((sample, index) => (
            <button type="button" className="btn" key={sample.label} onClick={() => fillWithSample(index)} disabled={busy}>
              Fill in a {sample.label.toLowerCase()}
            </button>
          ))}
        </div>
        {error && <Notice>{error}</Notice>}
        <div className="form__row">
          <button className="btn btn--primary" disabled={busy} onClick={() => onSend(editedDocument()?.body.innerHTML ?? "")}>
            {busy ? "Sending…" : "Send reply"}
          </button>
          <button className="btn" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
        </div>
      </div>
    </section>
  );
}

/** Tab (and Shift+Tab) jump between the rate cells instead of leaving the email. */
function moveToNextRateCell(doc: Document, event: KeyboardEvent): void {
  if (event.key !== "Tab") return;
  const selection = doc.getSelection();
  const node = selection?.anchorNode;
  const current = (node instanceof Element ? node : node?.parentElement)?.closest("td.rate");
  const cells = [...doc.querySelectorAll("td.rate")];
  const target = cells[cells.indexOf(current as Element) + (event.shiftKey ? -1 : 1)];
  if (!current || !target) return;
  event.preventDefault();
  const range = doc.createRange();
  range.selectNodeContents(target);
  range.collapse(false);
  selection?.removeAllRanges();
  selection?.addRange(range);
}
