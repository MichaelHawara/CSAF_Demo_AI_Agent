import type {
  Agent,
  AgentDetail,
  AttackResult,
  Cart,
  ControlStatus,
  Product,
  ProductDetail,
  SecurityEvent,
  XRayState,
} from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = await response.text();
    }
    throw new Error(detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  status: () => request<ControlStatus>("/api/control/status"),
  loadDemo: () => request<{ agent: Agent; demo_request: string; cart: Cart }>("/api/control/load-demo", { method: "POST" }),
  resetDemo: () => request<{ agent: Agent; demo_request: string; cart: Cart }>("/api/control/reset-demo", { method: "POST" }),
  products: () => request<Product[]>("/api/products"),
  searchProducts: (q: string, maximumPrice?: number) => {
    const params = new URLSearchParams({ q });
    if (maximumPrice != null) params.set("maximum_price", String(maximumPrice));
    return request<Product[]>(`/api/products/search?${params.toString()}`);
  },
  product: (id: string) => request<ProductDetail>(`/api/products/${id}`),
  cart: (customerId: string) => request<Cart>(`/api/cart/${customerId}`),
  addCartItem: (customerId: string, productId: string, quantity: number, agentId?: string) =>
    request<Cart>(`/api/cart/${customerId}/items`, {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity, agent_id: agentId }),
    }),
  removeCartItem: (customerId: string, itemId: string) =>
    request<Cart>(`/api/cart/${customerId}/items/${itemId}`, { method: "DELETE" }),
  agents: () => request<Agent[]>("/api/agents"),
  agent: (id: string) => request<AgentDetail>(`/api/agents/${id}`),
  createAgent: (body: Record<string, unknown>) =>
    request<Agent>("/api/agents", { method: "POST", body: JSON.stringify(body) }),
  patchAgent: (id: string, body: Record<string, unknown>) =>
    request<Agent>(`/api/agents/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteAgent: (id: string) => request<{ deleted: boolean }>(`/api/agents/${id}`, { method: "DELETE" }),
  resetAgent: (id: string) => request<Agent>(`/api/agents/${id}/reset`, { method: "POST" }),
  sendMessage: (id: string, content: string) =>
    request<{
      assistant_text: string;
      attack_result: AttackResult;
      xray: XRayState;
      provider: string;
      provider_note: string;
      agent: Agent;
      cart: Cart;
    }>(`/api/agents/${id}/messages`, { method: "POST", body: JSON.stringify({ content }) }),
  events: (id: string) => request<SecurityEvent[]>(`/api/agents/${id}/events`),
  requestCheckout: (customerId: string, agentId: string) =>
    request<Record<string, unknown>>("/api/checkout/request", {
      method: "POST",
      body: JSON.stringify({ customer_id: customerId, agent_id: agentId }),
    }),
  confirmCheckout: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>("/api/checkout/confirm", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
