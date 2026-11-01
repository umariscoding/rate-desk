import { useEffect, useState } from "react";

import type { DormRequest, ThreadMessage } from "../../api/types";
import { EmailPreview } from "../../components/EmailPreview";
import { Notice } from "../../components/Notice";
import { useReplyToRequest } from "../../hooks/useDormRequests";
import { ReplyEditor } from "./ReplyEditor";

interface Props {
  request: DormRequest;
  onBack: () => void;
}

/** One rate request as a conversation with the sales desk. "Reply all" on the latest message opens the grid to fill in. */
export function DormRequestPage({ request, onBack }: Props) {
  const [replying, setReplying] = useState(false);
  const reply = useReplyToRequest();
  const latestFromSales = [...request.thread].reverse().find((message) => message.sender === "salesperson");
  const lastIndex = request.thread.lastIndexOf(latestFromSales as ThreadMessage);

  useEffect(() => {
    if (replying) document.getElementById("reply-editor")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [replying]);

  const send = (html: string) =>
    reply.mutate({ caseId: request.id, replyText: html }, { onSuccess: () => setReplying(false) });

  return (
    <article className="stack">
      <section className="card">
        <div className="card__body">
          <button className="link" onClick={onBack}>
            ← Inbox
          </button>
          <div className="record-title">
            <h2>{request.company ?? "Rate request"}</h2>
          </div>
        </div>
      </section>
      {request.thread.map((message, index) => (
        <MessageCard
          key={index}
          message={message}
          onReplyAll={request.can_reply && !replying && index === lastIndex ? () => setReplying(true) : undefined}
        />
      ))}
      {replying && latestFromSales?.body_html && (
        <ReplyEditor
          to={latestFromSales.sender_name}
          subject={latestFromSales.subject ?? ""}
          quotedHtml={latestFromSales.body_html}
          quotedFrom={latestFromSales.sender_name}
          busy={reply.isPending}
          error={reply.error?.message ?? null}
          onSend={send}
          onCancel={() => setReplying(false)}
        />
      )}
      {!request.can_reply && (
        <Notice tone="info">You have replied. The sales desk will write back if anything needs fixing.</Notice>
      )}
    </article>
  );
}

function MessageCard({ message, onReplyAll }: { message: ThreadMessage; onReplyAll?: () => void }) {
  const mine = message.sender === "dorm";
  return (
    <section className="card">
      <header className="card__header card__header--bar">
        <h3 className="card__title">{mine ? "Your reply" : "Message from the sales desk"}</h3>
        {onReplyAll && (
          <button className="btn btn--primary" onClick={onReplyAll}>
            Reply all
          </button>
        )}
      </header>
      <div className="card__body">
        {message.body_html !== null ? (
          <EmailPreview email={{ subject: message.subject ?? "Your reply", body_html: message.body_html }} from={message.sender_name} />
        ) : (
          <pre className="original__text">{message.body_text}</pre>
        )}
      </div>
    </section>
  );
}
