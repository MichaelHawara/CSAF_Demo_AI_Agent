import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "./services/api";
import type { Agent, AttackResult, Cart, ConversationMessage, SecurityEvent, XRayState } from "./types";

export interface DemoState {
  agent: Agent | null;
  cart: Cart | null;
  messages: ConversationMessage[];
  events: SecurityEvent[];
  xray: XRayState | null;
  attackResult: AttackResult | null;
  busy: boolean;
  refresh: () => Promise<void>;
  selectAgent: (id: string) => Promise<void>;
  reset: () => Promise<void>;
}

const DemoContext = createContext<DemoState | null>(null);

export function useDemo() {
  const value = useContext(DemoContext);
  if (!value) {
    throw new Error("useDemo must be used inside DemoProvider");
  }
  return value;
}

export function DemoProvider({ children }: { children: ReactNode }) {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [cart, setCart] = useState<Cart | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [xray, setXray] = useState<XRayState | null>(null);
  const [attackResult, setAttackResult] = useState<AttackResult | null>(null);
  const [busy, setBusy] = useState(false);

  const loadAgent = useCallback(async (id: string) => {
    const detail = await api.agent(id);
    setAgent(detail);
    setCart(detail.cart);
    setMessages(detail.messages);
    setXray(detail.xray);
    setAttackResult(detail.attack_result || null);
    setEvents(await api.events(id));
  }, []);

  const refresh = useCallback(async () => {
    if (agent?.id) {
      await loadAgent(agent.id);
      return;
    }
    const demo = await api.loadDemo();
    await loadAgent(demo.agent.id);
  }, [agent?.id, loadAgent]);

  const selectAgent = useCallback(
    async (id: string) => {
      localStorage.setItem("nozama-agent-id", id);
      await loadAgent(id);
    },
    [loadAgent],
  );

  const reset = useCallback(async () => {
    if (!agent) return;
    await api.resetAgent(agent.id);
    await loadAgent(agent.id);
  }, [agent, loadAgent]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setBusy(true);
      try {
        const stored = localStorage.getItem("nozama-agent-id");
        const agents = await api.agents();
        const match = agents.find((row) => row.id === stored) || agents[0];
        if (match && !cancelled) {
          await loadAgent(match.id);
        } else if (!cancelled) {
          const demo = await api.loadDemo();
          await loadAgent(demo.agent.id);
        }
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadAgent]);

  const value = useMemo<DemoState>(
    () => ({
      agent,
      cart,
      messages,
      events,
      xray,
      attackResult,
      busy,
      refresh: async () => {
        setBusy(true);
        try {
          await refresh();
        } finally {
          setBusy(false);
        }
      },
      selectAgent,
      reset,
    }),
    [agent, cart, messages, events, xray, attackResult, busy, refresh, selectAgent, reset],
  );

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}
