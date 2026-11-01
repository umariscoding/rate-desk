import { useState } from "react";

import { Notice } from "../../components/Notice";
import { clientEmails } from "../../samples/samples";

interface Props {
  busy: boolean;
  error: string | null;
  onSubmit: (emailText: string) => void;
  onCancel: () => void;
}

export function NewCase({ busy, error, onSubmit, onCancel }: Props) {
  const [text, setText] = useState("");

  return (
    <section className="card">
      <header className="card__header">
        <h2 className="card__title">New request</h2>
      </header>
      <form
        className="card__body form"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit(text);
        }}
      >
        <p className="muted">
          Paste the client's email. The agents read it, ask the DORM for rates, check their reply and build the proposal. You
          approve each email before it is sent.
        </p>
        <label htmlFor="client-email" className="visually-hidden">
          Client email
        </label>
        <textarea
          id="client-email"
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={14}
          placeholder="Hi Umar, we'd love to bring our team to Lisbon…"
          disabled={busy}
        />
        <div className="form__row">
          <span className="muted">Sample emails:</span>
          {clientEmails.map((sample) => (
            <button type="button" className="btn" key={sample.label} onClick={() => setText(sample.text)}>
              {sample.label}
            </button>
          ))}
        </div>
        {error && <Notice>{error}</Notice>}
        <div className="form__row">
          <button className="btn btn--primary" type="submit" disabled={busy || text.trim() === ""}>
            {busy ? "Reading the email…" : "Read email"}
          </button>
          <button type="button" className="btn" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
}
