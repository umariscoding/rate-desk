import type { CaseDetail } from "../../api/types";
import { Step } from "../../components/Step";

export function ClientEmailStep({ detail }: { detail: CaseDetail }) {
  return (
    <Step title="Client email" by="You pasted it" state="done">
      <details className="original">
        <summary>Show the original email</summary>
        <pre className="original__text">{detail.source_email}</pre>
      </details>
    </Step>
  );
}
