import { useRef } from "react";

/** How an email body looks inside its frame. Shared with the reply editor so both read the same. */
export const EMAIL_STYLES =
  "body{font:14px/1.5 system-ui,sans-serif;color:#17212b;margin:12px}table{border-collapse:collapse;font-size:13px}td,th{border:1px solid #cfd6dd;padding:6px 10px}th{background:#eef2f6}td.rate{background:#fff8d6}td.ok{background:#e6f4ea}";

interface EmailLike {
  subject: string;
  body_html: string;
  to_name?: string;
  to_email?: string;
}

interface Props {
  email: EmailLike;
  from?: string;
}

/** Agent-written HTML is shown in a sandboxed frame: no scripts run, and it cannot touch the page. */
export function EmailPreview({ email, from }: Props) {
  const frame = useRef<HTMLIFrameElement>(null);

  const fitToContent = () => {
    const body = frame.current?.contentDocument?.body;
    if (frame.current && body) frame.current.style.height = `${body.scrollHeight + 24}px`;
  };

  return (
    <article className="mail">
      <dl className="mail__meta">
        {from && (
          <>
            <dt>From</dt>
            <dd>{from}</dd>
          </>
        )}
        {email.to_name && (
          <>
            <dt>To</dt>
            <dd>
              {email.to_name} &lt;{email.to_email}&gt;
            </dd>
          </>
        )}
        <dt>Subject</dt>
        <dd>{email.subject}</dd>
      </dl>
      <iframe
        ref={frame}
        className="mail__body"
        title={email.subject}
        sandbox="allow-same-origin"
        srcDoc={`<style>${EMAIL_STYLES}</style>${email.body_html}`}
        onLoad={fitToContent}
      />
    </article>
  );
}
