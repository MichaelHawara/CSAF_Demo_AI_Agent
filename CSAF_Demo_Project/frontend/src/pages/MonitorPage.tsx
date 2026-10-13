import { SecuritySummary } from "../components/SecuritySummary";
import { EventFeed } from "../components/EventFeed";
import { OperatorTabs } from "../components/OperatorTabs";
import { useDemo, useLiveSync } from "../demoContext";

export function MonitorPage() {
  const demo = useDemo();
  useLiveSync();
  return (
    <div className="page">
      <OperatorTabs />
      <h1>Security Activity Monitor</h1>
      <p className="muted">
        Terminal-style feed of user, agent, catalog, policy, and result events. Secrets, cookies,
        and payment data are never written here. Updates live while the shopper uses Alex.
      </p>
      {demo.agent ? (
        <p>
          Monitoring agent: <strong>{demo.agent.display_name}</strong>{" "}
          <span className="muted">
            ({demo.agent.id} · {demo.agent.mode} · {demo.agent.provider}). Change it on the Control
            page; every tab follows.
          </span>
        </p>
      ) : null}
      <SecuritySummary result={demo.requestSummary} />
      <EventFeed events={demo.events} />
    </div>
  );
}
