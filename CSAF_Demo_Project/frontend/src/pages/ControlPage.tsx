import { FormEvent, useEffect, useState } from "react";
import { useDemo } from "../demoContext";
import { api } from "../services/api";
import type { Agent, AgentDetail } from "../types";
import { EventFeed } from "../components/EventFeed";
import { OperatorTabs } from "../components/OperatorTabs";

export function ControlPage() {
  const demo = useDemo();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [detail, setDetail] = useState<AgentDetail | null>(null);
  const [name, setName] = useState("Alex lab instance");
  const [provider, setProvider] = useState("mock");
  const [mode, setMode] = useState("vulnerable");
  const [error, setError] = useState("");

  async function refreshList() {
    setAgents(await api.agents());
    if (demo.agent) {
      setDetail(await api.agent(demo.agent.id));
    }
  }

  useEffect(() => {
    refreshList().catch((err) => setError(String(err)));
  }, [demo.agent?.id]);

  async function create(event: FormEvent) {
    event.preventDefault();
    const created = await api.createAgent({
      display_name: name,
      provider,
      mode,
      budget: 80,
      max_quantity: 1,
    });
    await demo.selectAgent(created.id);
    await refreshList();
  }

  async function select(id: string) {
    await demo.selectAgent(id);
    setDetail(await api.agent(id));
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
          {agents.map((agent) => (
            <div
              key={agent.id}
              className={`list-item ${demo.agent?.id === agent.id ? "active" : ""}`}
              onClick={() => select(agent.id)}
            >
              <strong>{agent.display_name}</strong>
              <div className="muted">
                {agent.mode} · {agent.provider}
              </div>
            </div>
          ))}
          <form onSubmit={create} className="field" style={{ marginTop: 12 }}>
            <label>
              Display name
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label>
              Provider
              <select value={provider} onChange={(e) => setProvider(e.target.value)}>
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
              <h3>{demo.agent.display_name}</h3>
              <p>
                Agent ID: {demo.agent.id}
                <br />
                Customer ID: {demo.agent.customer_id}
                <br />
                Model: {demo.agent.model}
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
                    await api.loadDemo();
                    await demo.refresh();
                    await refreshList();
                  }}
                >
                  Delete agent
                </button>
              </div>
              <p>{demo.agent.provider_note}</p>
              <h4>System instruction</h4>
              <pre className="wrap">{demo.agent.system_instruction}</pre>
              <h4>Allowed tools</h4>
              <p>{demo.agent.allowed_tools.join(", ")}</p>
              <h4>Current cart</h4>
              <pre className="wrap">{JSON.stringify(detail?.cart || demo.cart, null, 2)}</pre>
              <h4>Conversation</h4>
              <pre className="wrap">{JSON.stringify(detail?.messages || demo.messages, null, 2)}</pre>
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
