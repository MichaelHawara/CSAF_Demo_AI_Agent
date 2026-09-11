import type { SecurityEvent } from "../types";

export function EventFeed({ events }: { events: SecurityEvent[] }) {
  return (
    <div className="terminal" aria-label="Security activity monitor">
      {events.length === 0 ? <div># waiting for agent activity</div> : null}
      {events.map((event) => (
        <div key={event.id} className={event.actor}>
          {event.formatted}
        </div>
      ))}
    </div>
  );
}
