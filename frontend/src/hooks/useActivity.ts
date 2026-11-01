import { useEffect, useState } from "react";

import { activityUrl } from "../api/http";
import type { ActivityEvent } from "../api/types";

/**
 * Events that share a key describe one step: the newest replaces the older in place. Cominty gives a step's start
 * and end different ids, so a finished event also closes the running one with the same source and label.
 */
export function coalesce(events: ActivityEvent[], incoming: ActivityEvent): ActivityEvent[] {
  const closesRunning = (event: ActivityEvent) =>
    incoming.state !== "running" &&
    event.state === "running" &&
    event.source === incoming.source &&
    event.label === incoming.label;
  const index = events.findIndex((event) => event.key === incoming.key || closesRunning(event));
  if (index === -1) return [...events, incoming];
  return events.map((event, position) => (position === index ? incoming : event));
}

/** Follows what the agents are doing for a case. The server replays history first, so reloads lose nothing. */
export function useActivity(caseId: string | null): ActivityEvent[] {
  const [events, setEvents] = useState<ActivityEvent[]>([]);

  useEffect(() => {
    setEvents([]);
    if (caseId === null) return;
    const source = new EventSource(activityUrl(caseId));
    source.onmessage = (message) => {
      const incoming = JSON.parse(message.data) as ActivityEvent;
      setEvents((current) => coalesce(current, incoming));
    };
    return () => source.close();
  }, [caseId]);

  return events;
}
