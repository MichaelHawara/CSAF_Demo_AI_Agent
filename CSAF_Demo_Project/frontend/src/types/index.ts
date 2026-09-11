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
  image_alt_text_public: string;
}

export interface Review {
  id: string;
  author: string;
  rating: number;
  body: string;
}

export interface ProductDetail extends Product {
  reviews: Review[];
}

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  line_total: number;
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
  budget: number;
  max_quantity: number;
  status: string;
  created_at: string;
  gemini_available: boolean;
  provider_note: string;
}

export interface AgentDetail extends Agent {
  cart: Cart;
  messages: ConversationMessage[];
  xray: XRayState;
  attack_result: AttackResult | Record<string, never>;
}

export interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  tool_name: string;
  created_at: string;
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

export interface AttackResult {
  banner?: string;
  requested_quantity?: number;
  cart_quantity?: number;
  budget?: number;
  cart_total?: number;
  confirmation_received?: boolean;
  attempted_quantity?: number;
  attempted_total?: number;
  allowed_quantity?: number;
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
    checkout_requests?: Array<Record<string, unknown>>;
    blocked_actions?: Array<{ tool: string; reason?: string }>;
    final_result?: AttackResult;
  };
  hidden_content?: Record<string, string> | null;
  current_step?: number;
}

export interface ControlStatus {
  gemini_configured: boolean;
  effective_provider: string;
  demo_agent_id: string;
  demo_customer_id: string;
  demo_request: string;
  budget: number;
  max_quantity: number;
  checkout_confirmation: string;
  deterministic_demo_mode: boolean;
  reserved_endpoints: Record<string, string>;
}
