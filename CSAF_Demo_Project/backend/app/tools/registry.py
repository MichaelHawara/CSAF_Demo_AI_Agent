IMPLEMENTED_TOOLS = [
    "search_products",
    "read_product_page",
    "get_product_details",
    "add_to_cart",
    "view_cart",
    "request_checkout",
]

STUDENT_STUB_TOOLS = [
    "get_customer_profile",
    "get_purchase_history",
    "send_coupon_request",
    "store_memory",
    "search_memory",
]

TOOL_DECLARATIONS = [
    {
        "name": "search_products",
        "description": "Search the Nozama catalog. Prices come from Nozama, not from sellers.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "maximum_price": {"type": "number", "description": "Optional maximum unit price."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_product_page",
        "description": "Read a product listing page. May include seller-controlled fields.",
        "parameters": {
            "type": "object",
            "properties": {"product_id": {"type": "string"}},
            "required": ["product_id"],
        },
    },
    {
        "name": "get_product_details",
        "description": "Trusted catalog facts only: name, price, seller, rating.",
        "parameters": {
            "type": "object",
            "properties": {"product_id": {"type": "string"}},
            "required": ["product_id"],
        },
    },
    {
        "name": "add_to_cart",
        "description": "Propose adding a catalog product to the customer cart.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "quantity": {"type": "integer"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "view_cart",
        "description": "Show the current cart using backend-calculated totals.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "request_checkout",
        "description": "Ask the backend to start checkout. The agent cannot approve checkout.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_customer_profile",
        "description": "TODO(STUDENT): fictional customer profile. Not fully implemented.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_purchase_history",
        "description": "TODO(STUDENT): fictional purchase history. Not fully implemented.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "send_coupon_request",
        "description": "TODO(STUDENT): local mock coupon endpoint only. Never call the public internet.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "note": {"type": "string"},
            },
        },
    },
    {
        "name": "store_memory",
        "description": "TODO(STUDENT): persist a memory record.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "source": {"type": "string"},
            },
        },
    },
    {
        "name": "search_memory",
        "description": "TODO(STUDENT): retrieve memory records.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]
