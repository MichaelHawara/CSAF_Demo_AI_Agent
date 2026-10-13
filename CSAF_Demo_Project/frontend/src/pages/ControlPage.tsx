import { FormEvent, useEffect, useState } from "react";
import { useDemo, useLiveSync } from "../demoContext";
import { api } from "../services/api";
import type { Agent } from "../types";
import { SecuritySummary } from "../components/SecuritySummary";
import { EventFeed } from "../components/EventFeed";
import { OperatorTabs } from "../components/OperatorTabs";

export function ControlPage() {
  const demo = useDemo();
  useLiveSync();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [name, setName] = useState("Alex lab instance");
  const [provider, setProvider] = useState("mock");
  const [providerTouched, setProviderTouched] = useState(false);
  const [mode, setMode] = useState("vulnerable");
  const [error, setError] = useState("");

  async function refreshList() {
    setAgents(await api.agents());
  }

  // New agents default to whatever the backend is configured to use (Gemini when a key is set).
  useEffect(() => {
    api
      .status()
      .then((status) => {
        if (!providerTouched) setProvider(status.effective_provider);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    refreshList().catch((err) => setError(String(err)));
    // Agents can also be created or removed from another tab.
    const timer = window.setInterval(() => refreshList().catch(() => undefined), 5000);
    return () => window.clearInterval(timer);
  }, [demo.agent?.id]);

  async function create(event: FormEvent) {
    event.preventDefault();
    const created = await api.createAgent({
      display_name: name,
      provider,
      mode,
    });
    await demo.selectAgent(created.id);
    await refreshList();
  }

  async function select(id: string) {
    await demo.selectAgent(id);
  }

  async function saveMode(next: string) {
    if (!demo.agent) return;
    await api.patchAgent(demo.agent.id, { mode: next });
    await demo.refresh();
    await refreshList();
  }

  async function saveProvider(next: string) {
    if (!demo.agent) return;
    await api.patchAgent(demo.agent.id, { provider: next });
    await demo.refresh();
    await refreshList();
  }

  return (
    <div className="page">
      <OperatorTabs />
      <h1>Agent Control Center</h1>
      <p className="muted">
        Creating an agent creates a configuration and memory space. It does not train a new model.
      </p>
      {error ? <p>{error}</p> : null}
      <div className="control-grid">
        <div className="card">
          <h3>Agents</h3>
          <p className="muted">
            The selected agent is the one Alex, the Monitor and X-Ray use, in every open tab.
          </p>
          {agents.map((agent) => {
            const selected = demo.agent?.id === agent.id;
            return (
              <div key={agent.id} className={`list-item agent-row ${selected ? "active" : ""}`}>
                <div className="agent-row-info">
                  <strong>{agent.display_name}</strong>
                  <div className="muted">
                    {agent.mode} · {agent.provider}
                  </div>
                </div>
                {selected ? (
                  <span className="badge trusted">Selected</span>
                ) : (
                  <button
                    type="button"
                    className="btn secondary"
                    onClick={() => select(agent.id)}
                    aria-label={`Select agent ${agent.display_name}`}
                  >
                    Select agent
                  </button>
                )}
              </div>
            );
          })}
          <form onSubmit={create} className="field" style={{ marginTop: 12 }}>
            <label>
              Display name
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label>
              Provider
              <select value={provider} onChange={(e) => {
                  setProviderTouched(true);
                  setProvider(e.target.value);
                }}>
                <option value="mock">mock</option>
                <option value="gemini">gemini</option>
              </select>
            </label>
            <label>
              Mode
              <select value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="vulnerable">vulnerable</option>
                <option value="patched">patched</option>
              </select>
            </label>
            <button className="btn" type="submit">
              Create agent instance
            </button>
          </form>
        </div>
        <div>
          {demo.agent ? (
            <div className="card">
              <h3>
                {demo.agent.display_name} <span className="badge trusted">Selected agent</span>
              </h3>
              <p>
                Agent ID: {demo.agent.id}
                <br />
                Customer ID: {demo.agent.customer_id}
                <br />
                Model: {demo.agent.model}
                <br />
                Detected from last request: budget{" "}
                {demo.agent.detected_budget ? `$${demo.agent.detected_budget.toFixed(2)}` : "none"}, quantity{" "}
                {demo.agent.detected_quantity || "none"}
                <br />
                Created: {demo.agent.created_at}
              </p>
              <div className="row">
                <button className="btn secondary" type="button" onClick={() => saveProvider("mock")}>
                  Use mock
                </button>
                <button className="btn secondary" type="button" onClick={() => saveProvider("gemini")}>
                  Use Gemini
                </button>
                <button className="btn danger" type="button" onClick={() => saveMode("vulnerable")}>
                  Vulnerable mode
                </button>
                <button className="btn" type="button" onClick={() => saveMode("patched")}>
                  Patched mode
                </button>
                <button className="btn ghost" type="button" onClick={() => demo.reset()}>
                  Reset agent
                </button>
                <button
                  className="btn danger"
                  type="button"
                  onClick={async () => {
                    await api.deleteAgent(demo.agent!.id);
                    const fresh = await api.loadDemo();
                    await demo.selectAgent(fresh.agent.id);
                    await refreshList();
                  }}
                >
                  Delete agent
                </button>
              </div>
              <p>{demo.agent.provider_note}</p>
              <SecuritySummary result={demo.requestSummary} />
              <h4>System instruction</h4>
              <pre className="wrap">{demo.agent.system_instruction}</pre>
              <h4>Allowed tools</h4>
              <p>{demo.agent.allowed_tools.join(", ")}</p>
              <h4>Current cart</h4>
              <pre className="wrap">{JSON.stringify(demo.cart, null, 2)}</pre>
              <h4>Conversation</h4>
              <pre className="wrap">{JSON.stringify(demo.messages, null, 2)}</pre>
              <h4>Activity events</h4>
              <EventFeed events={demo.events} />
            </div>
          ) : (
            <p>Select or create an agent.</p>
          )}
        </div>
      </div>
    </div>
  );
}
