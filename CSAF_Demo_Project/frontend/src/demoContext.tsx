import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api } from "./services/api";
import type {
  Agent,
  RequestSummary,
  Cart,
  CheckoutReceipt,
  ConversationMessage,
  SecurityEvent,
  XRayState,
} from "./types";

export interface DemoState {
  agent: Agent | null;
  cart: Cart | null;
  messages: ConversationMessage[];
  events: SecurityEvent[];
  xray: XRayState | null;
  requestSummary: RequestSummary | null;
  /** The last checkout the customer approved (null until they approve one). */
  checkoutReceipt: CheckoutReceipt | null;
  busy: boolean;
  refresh: () => Promise<void>;
  /** Reload the current agent without flipping `busy` (used for live polling). */
  sync: () => Promise<void>;
  selectAgent: (id: string) => Promise<void>;
  reset: () => Promise<void>;
}

// The Shop, Control and Monitor pages usually live in different browser tabs.
// Remembering the chosen agent here (and watching for changes from other tabs)
// keeps every tab on the same agent, so the Monitor shows what Alex is doing.
const SELECTED_AGENT_KEY = "nozama.selectedAgent";

function storedAgentId(): string | null {
  try {
    return window.localStorage.getItem(SELECTED_AGENT_KEY);
  } catch {
    return null;
  }
}

function rememberAgentId(id: string) {
  try {
    window.localStorage.setItem(SELECTED_AGENT_KEY, id);
  } catch {
    // Storage can be unavailable (private mode); selection still works in this tab.
  }
}

const DemoContext = createContext<DemoState | null>(null);

export function useDemo() {
  const value = useContext(DemoContext);
  if (!value) {
    throw new Error("useDemo must be used inside DemoProvider");
  }
  return value;
}

/**
 * Keep an operator page (Monitor / Control / X-Ray) current. These pages live
 * in their own browser tab, so without polling they would not see what the
 * shopper does in the Alex panel.
 */
export function useLiveSync(intervalMs = 3000) {
  const { sync } = useDemo();
  useEffect(() => {
    const timer = window.setInterval(() => {
      sync().catch(() => undefined);
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [sync, intervalMs]);
}

export function DemoProvider({ children }: { children: ReactNode }) {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [cart, setCart] = useState<Cart | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [xray, setXray] = useState<XRayState | null>(null);
  const [requestSummary, setRequestSummary] = useState<RequestSummary | null>(null);
  const [checkoutReceipt, setCheckoutReceipt] = useState<CheckoutReceipt | null>(null);
  const [busy, setBusy] = useState(false);

  // The agent this tab is currently showing. Slow responses for a previously
  // selected agent are dropped so they cannot overwrite the new selection.
  const activeId = useRef<string | null>(null);

  const loadAgent = useCallback(async (id: string, select = false) => {
    const previous = activeId.current;
    if (select) activeId.current = id;
    let detail: Awaited<ReturnType<typeof api.agent>>;
    let feed: SecurityEvent[];
    try {
      detail = await api.agent(id);
      feed = await api.events(id);
    } catch (err) {
      // Selecting an agent that no longer exists must not strand this tab.
      if (select && activeId.current === id) activeId.current = previous;
      throw err;
    }
    if (activeId.current !== id) return;
    setAgent(detail);
    setCart(detail.cart);
    setMessages(detail.messages);
    setXray(detail.xray);
    setRequestSummary(detail.request_summary || null);
    setCheckoutReceipt(detail.checkout_receipt || null);
    setEvents(feed);
  }, []);

  const refresh = useCallback(async () => {
    if (agent?.id) {
      await loadAgent(agent.id, true);
      return;
    }
    const demo = await api.loadDemo();
    rememberAgentId(demo.agent.id);
    await loadAgent(demo.agent.id, true);
  }, [agent?.id, loadAgent]);

  const sync = useCallback(async () => {
    // Another tab may have picked a different agent since the last poll.
    const chosen = storedAgentId();
    if (chosen && chosen !== activeId.current) {
      try {
        await loadAgent(chosen, true);
        return;
      } catch {
        // That agent no longer exists (deleted). Stay on the current one.
        if (agent?.id) rememberAgentId(agent.id);
      }
    }
    if (agent?.id) await loadAgent(agent.id, true);
  }, [agent?.id, loadAgent]);

  const selectAgent = useCallback(
    async (id: string) => {
      await loadAgent(id, true);
      rememberAgentId(id);
    },
    [loadAgent],
  );

  const reset = useCallback(async () => {
    if (!agent) return;
    await api.resetAgent(agent.id);
    await loadAgent(agent.id, true);
  }, [agent, loadAgent]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setBusy(true);
      try {
        const status = await api.status();
        const agents = await api.agents();
        const remembered = agents.find((row) => row.id === storedAgentId());
        const match =
          remembered || agents.find((row) => row.id === status.demo_agent_id) || agents[0];
        if (match && !cancelled) {
          rememberAgentId(match.id);
          await loadAgent(match.id, true);
        } else if (!cancelled) {
          const demo = await api.loadDemo();
          rememberAgentId(demo.agent.id);
          await loadAgent(demo.agent.id, true);
        }
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadAgent]);

  // Switch immediately when another tab selects an agent.
  useEffect(() => {
    function onStorage(event: StorageEvent) {
      if (event.key === SELECTED_AGENT_KEY && event.newValue && event.newValue !== activeId.current) {
        loadAgent(event.newValue, true).catch(() => undefined);
      }
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [loadAgent]);

  // Switch immediately when another tab selects an agent.
  useEffect(() => {
    function onStorage(event: StorageEvent) {
      if (event.key === SELECTED_AGENT_KEY && event.newValue && event.newValue !== activeId.current) {
        loadAgent(event.newValue, true).catch(() => undefined);
      }
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [loadAgent]);

  const value = useMemo<DemoState>(
    () => ({
      agent,
      cart,
      messages,
      events,
      xray,
      requestSummary,
      checkoutReceipt,
      busy,
      refresh: async () => {
        setBusy(true);
        try {
          await refresh();
        } finally {
          setBusy(false);
        }
      },
      sync,
      selectAgent,
      reset,
    }),
    [agent, cart, messages, events, xray, requestSummary, checkoutReceipt, busy, refresh, sync, selectAgent, reset],
  );

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}
