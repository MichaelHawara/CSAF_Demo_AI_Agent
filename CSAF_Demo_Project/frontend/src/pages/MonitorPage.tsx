import { EventFeed } from "../components/EventFeed";
import { useDemo } from "../demoContext";

export function MonitorPage() {
  const demo = useDemo();
  return (
    <div className="page">
      <h1>Security Activity Monitor</h1>
      <p className="muted">
        Terminal-style feed of user, agent, catalog, policy, and result events. Secrets, cookies,
        and payment data are never written here.
      </p>
      <EventFeed events={demo.events} />
    </div>
  );
}
