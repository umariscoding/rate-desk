import type { ReactNode } from "react";

import type { Tone } from "../lib/format";

interface Props {
  tone?: Tone;
  title?: string;
  children: ReactNode;
}

export function Notice({ tone = "warn", title, children }: Props) {
  return (
    <div className={`notice notice--${tone}`} role={tone === "warn" ? "alert" : undefined}>
      {title && <strong className="notice__title">{title}</strong>}
      <div>{children}</div>
    </div>
  );
}
