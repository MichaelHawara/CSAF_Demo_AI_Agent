export interface Product {
  id: string;
  name: string;
  seller_id: string;
  seller_name: string;
  trusted_seller: boolean;
  price: number;
  rating: number;
  review_count: number;
  description: string;
  category: string;
  accent: string;
  url: string;
}

export interface Review {
  id: string;
  author: string;
  rating: number;
  body: string;
}

export interface ProductDetail extends Product {
  reviews: Review[];
  image_alt_text_public?: string;
}

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  image_url?: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface ReceiptLine {
  product_id: string;
  name: string;
  image_url?: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

/** What the customer approved. Computed by the backend from catalog prices. */
export interface CheckoutReceipt {
  order_id: string;
  approved_at: string;
  status: string;
  items: ReceiptLine[];
  item_count: number;
  subtotal: number;
  tax_rate: number;
  tax: number;
  shipping: number;
  total: number;
  demo_notice: string;
  real_purchase: boolean;
}

export interface Cart {
  id: string;
  customer_id: string;
  status: string;
  demo_checked_out: boolean;
  items: CartItem[];
  total: number;
  quantity: number;
}

export interface Agent {
  id: string;
  customer_id: string;
  display_name: string;
  provider: string;
  model: string;
  mode: "vulnerable" | "patched" | string;
  system_instruction: string;
  allowed_tools: string[];
  /** Limits the backend read from the customer's latest message. Never preset. */
  detected_budget?: number | null;
  detected_quantity?: number | null;
  status: string;
  created_at: string;
  gemini_available: boolean;
  provider_note: string;
}

export interface AgentDetail extends Agent {
  cart: Cart;
  messages: ConversationMessage[];
  xray: XRayState;
  request_summary: RequestSummary | Record<string, never>;
  checkout_receipt: CheckoutReceipt | null;
}

export interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  tool_name: string;
  created_at: string;
  /** Product cards shown under an assistant reply. */
  attachments?: { products: Product[]; quantity: number } | null;
}

export interface SecurityEvent {
  id: string;
  actor: string;
  message: string;
  details: string;
  step: number;
  created_at: string;
  formatted: string;
}

export interface RequestSummary {
  /** Neutral, plain-language lines describing what the monitor recorded. */
  security_summary?: string[];
  /** Quantity / budget the customer asked for in their message (null when not stated). */
  requested_quantity?: number | null;
  budget?: number | null;
  /** Units and dollars the agent added to the cart during this request. */
  added_quantity?: number;
  added_total?: number;
  cart_quantity?: number;
  cart_total?: number;
  confirmation_received?: boolean;
  attempted_quantity?: number;
  attempted_total?: number;
  allowed_quantity?: number | null;
  mode?: string;
  demo_notice?: string;
}

export interface ContextSection {
  label: string;
  text: string;
  trusted: boolean;
  highlight: boolean;
}

export interface XRayState {
  shopper?: {
    request?: string;
    search_results?: Product[];
    product_being_read?: Record<string, unknown> | null;
    visible_description?: string;
    cart?: Cart | null;
  };
  ai_context?: ContextSection[];
  system?: {
    model_requests?: unknown[];
    tool_calls?: Array<{ name: string; arguments: Record<string, unknown>; blocked: boolean }>;
    policy_decisions?: string[];
    cart_modifications?: unknown[];
    /** Simulated transfers. They only ever reach the in-process Local Demo Endpoint. */
    data_transfer?: Array<{
      tool: string;
      ok: boolean;
      blocked: boolean;
      destination: string | null;
      network_request: boolean;
    }>;
    checkout_requests?: Array<Record<string, unknown>>;
    blocked_actions?: Array<{ tool: string; reason?: string }>;
    final_result?: RequestSummary;
  };
  hidden_content?: Record<string, string> | null;
  current_step?: number;
}

export interface DemoLoad {
  agent: Agent;
  cart: Cart;
  /** A random request generated from the product catalog. */
  demo_request: string;
  demo_request_details: {
    request: string;
    category: string;
    product_id: string;
    product_name: string;
    quantity: number;
    budget: number;
  } | null;
}

export interface ControlStatus {
  gemini_configured: boolean;
  effective_provider: string;
  demo_agent_id: string;
  demo_customer_id: string;
  /** How many catalog-based requests the Load Demo Request button can pick from. */
  demo_request_count: number;
  checkout_confirmation: string;
  deterministic_demo_mode: boolean;
  reserved_endpoints: Record<string, string>;
}
