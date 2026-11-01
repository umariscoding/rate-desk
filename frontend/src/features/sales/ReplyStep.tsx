import type { CaseDetail } from "../../api/types";
import { EmailPreview } from "../../components/EmailPreview";
import { Notice } from "../../components/Notice";
import { Step } from "../../components/Step";
import { DORM_LABEL } from "../../lib/format";

interface Props {
  detail: CaseDetail;
}

export function ReplyStep({ detail }: Props) {
  const title = `Reply from ${DORM_LABEL}`;
  const latest = detail.dorm_replies.at(-1);
  const isHtml = detail.dorm_replies_are_html.at(-1) ?? false;
  if (detail.status === "awaiting_dorm_reply" || detail.status === "awaiting_dorm_correction") {
    return (
      <Step title={title} by={DORM_LABEL} state="active">
        {latest && <ReplyText text={latest} isHtml={isHtml} />}
        <Notice tone="info">
          Waiting for {DORM_LABEL} to reply. They see your request in their inbox, and it will appear here when they answer.
        </Notice>
      </Step>
    );
  }
  if (!latest) {
    return <Step title={title} by={DORM_LABEL} state="waiting" hint="Arrives after you send the rate request." />;
  }
  return (
    <Step title={title} by={DORM_LABEL} state="done">
      <ReplyText text={latest} isHtml={isHtml} />
    </Step>
  );
}

function ReplyText({ text, isHtml }: { text: string; isHtml: boolean }) {
  return (
    <details className="original">
      <summary>Show their reply</summary>
      {isHtml ? <EmailPreview email={{ subject: "Reply from the DORM", body_html: text }} from={`${DORM_LABEL}`} /> : <pre className="original__text">{text}</pre>}
    </details>
  );
}
