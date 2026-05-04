import sqlite3
from pathlib import Path
from semantic_router import Route, SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

db_path = Path(__file__).parent / "db.sqlite"

# ─────────────────────────────────────────────
# 🔹 ENCODER
# ─────────────────────────────────────────────
encoder = HuggingFaceEncoder(
    name='sentence-transformers/all-MiniLM-L6-v2'
)

# ─────────────────────────────────────────────
# 🔹 FAQ ROUTE
# Semantic router is only used for FAQ detection now.
# Product queries are handled by DB check + intent check.
# ─────────────────────────────────────────────
faq = Route(
    name='faq',
    utterances=[
        "what is your return policy",
        "how can i return a product",
        "can i return items",
        "return criteria",
        "return conditions",
        "how long do i have to return",

        "refund time",
        "how long does refund take",
        "when will i get refund",

        "payment methods",
        "do you accept cash on delivery",
        "do you support cod",
        "can i pay using upi",
        "credit card payment",

        "track my order",
        "how to track order",
        "order tracking details",

        "defective product",
        "damaged item",
        "broken product",
        "faulty item"
    ],
    score_threshold=0.25
)

# ─────────────────────────────────────────────
# 🔹 SQL ROUTE
# Kept for semantic fallback only.
# ─────────────────────────────────────────────
sql = Route(
    name='sql',
    utterances=[
        "show me products",
        "find products",
        "search for items",
        "browse products",
        "products under 5000",
        "items under budget",
        "filter products by price",
        "cheap products",
        "expensive items",
        "top rated products",
        "best products",
        "popular products",
        "available products",
        "product details",
        "items available",
    ],
    score_threshold=0.35
)

# ─────────────────────────────────────────────
# 🔹 SEMANTIC ROUTER
# ─────────────────────────────────────────────
router = SemanticRouter(
    routes=[faq, sql],
    encoder=encoder,
    auto_sync="local"
)


# ─────────────────────────────────────────────
# 🔹 STEP 1 — DB CHECK
# Check if any word in query matches a real
# product title, brand or category in the DB.
# This is the most reliable product detection.
# e.g. "premium smartwatches" → "smartwatches"
#       found in category → SQL
# ─────────────────────────────────────────────
def is_product_query(query: str) -> bool:
    words = [w for w in query.lower().split() if len(w) > 2]
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for word in words:
                cursor.execute("""
                    SELECT 1 FROM product
                    WHERE LOWER(category) LIKE ?
                    OR LOWER(brand) LIKE ?
                    OR LOWER(title) LIKE ?
                    LIMIT 1
                """, (f'%{word}%', f'%{word}%', f'%{word}%'))
                if cursor.fetchone():
                    return True
    except Exception as e:
        print(f"[DB CHECK ERROR] {e}")
    return False


# ─────────────────────────────────────────────
# 🔹 STEP 2 — INTENT CHECK
# If product not in DB but query LOOKS like a
# product search (has intent words like show,
# find, cheap, under etc.) → still route to SQL.
# SQL chain will respond with "product not found".
# e.g. "show me gucci bags" → not in DB
#       but "show" signals product intent → SQL
# ─────────────────────────────────────────────
PRODUCT_INTENT_WORDS = {
    "show", "find", "search", "buy", "get", "give", "list",
    "cheap", "best", "top", "affordable", "premium", "expensive",
    "budget", "discounted", "under", "above", "price", "cheapest",
    "popular", "rated", "deals", "sale", "offers", "available"
}

def is_product_intent(query: str) -> bool:
    words = set(query.lower().split())
    return bool(words & PRODUCT_INTENT_WORDS)


# ─────────────────────────────────────────────
# 🔹 STEP 3 — FAQ KEYWORD CHECK
# Hard block for clear FAQ queries so they
# never accidentally route to SQL.
# ─────────────────────────────────────────────
FAQ_KEYWORDS = {
    "return", "refund", "policy", "track", "payment",
    "damage", "defective", "cod", "upi", "cancel",
    "exchange", "warranty", "complaint", "delivery issue"
}

def is_faq_query(query: str) -> bool:
    words = set(query.lower().split())
    return bool(words & FAQ_KEYWORDS)


# ─────────────────────────────────────────────
# 🔹 FINAL ROUTE DETECTION
#
# Flow:
#   1. FAQ keyword check  → faq  (hard block)
#   2. DB check           → sql  (most reliable)
#   3. Intent check       → sql  (product not in DB)
#   4. Semantic router    → faq  (last resort)
#   5. Default            → faq
# ─────────────────────────────────────────────
def detect_route(query: str) -> str:
    query_lower = query.lower().strip()

    # Step 1: Hard block FAQ keywords first
    # Prevents "show me return policy" going to SQL
    if is_faq_query(query_lower):
        return "faq"

    # Step 2: DB check — most reliable product detection
    # "premium smartwatches", "NOVA hair dryer", "havells"
    # all match something in DB → SQL
    if is_product_query(query_lower):
        return "sql"

    # Step 3: Intent check — product not in DB but looks like search
    # "show me gucci bags" → sql (will say not found)
    if is_product_intent(query_lower):
        return "sql"

    # Step 4: Semantic router — for ambiguous queries
    route = router(query_lower)
    if route and route.name:
        return route.name

    # Step 5: Safe default
    return "faq"


# ─────────────────────────────────────────────
# 🔹 TEST
# ─────────────────────────────────────────────
if __name__ == '__main__':
    queries = [
        # ── Should go to SQL ──
        "premium smartwatches",          # adjective + category
        "NOVA hair dryer",               # brand in DB
        "havells hair dryer",            # brand in DB
        "show me 10 laptops",            # intent word
        "budget friendly headphones",    # adjective
        "top rated samsung phones",      # brand + adjective
        "pink hair dryer",               # color + product
        "show me gucci bags",            # not in DB but intent word
        "affordable shoes under 1000",   # adjective + price

        # ── Should go to FAQ ──
        "what is your return policy",
        "do you support COD",
        "how long does refund take",
        "track my order",
        "damaged item received",

        # ── Edge cases ──
        "show me chargers where return is available",  # has both — FAQ wins (return keyword)
        "headphones available",                        # in DB → SQL
    ]

    print(f"{'Query':<45} {'Route'}")
    print("-" * 55)
    for q in queries:
        print(f"{q:<45} → {detect_route(q)}")