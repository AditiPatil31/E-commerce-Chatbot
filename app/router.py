import sqlite3
from pathlib import Path
from semantic_router import Route,SemanticRouter
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
# Rich utterances covering FAQ queries that
# contain product words like "track my product",
# "return my item", "money back process" etc.
# ─────────────────────────────────────────────
faq = Route(
    name='faq',
    utterances=[
        # Return
        "what is your return policy",
        "how can i return a product",
        "can i return items",
        "return criteria",
        "return conditions",
        "how long do i have to return",
        "return my order",
        "return my product",
        "i want to return my item",
        "return process for damaged product",
        "how to return a defective item",

        # Refund
        "refund time",
        "how long does refund take",
        "when will i get refund",
        "money back process",
        "how to get my money back",
        "refund for my order",
        "refund status",
        "what is money back process",

        # Payment
        "payment methods",
        "do you accept cash on delivery",
        "do you support cod",
        "can i pay using upi",
        "credit card payment",
        "payment options available",
        "how can i pay",

        # Tracking
        "track my order",
        "how to track order",
        "order tracking details",
        "where is my order",
        "how to track my product",
        "how can i track my product",
        "track my delivery",
        "when will my order arrive",
        "order status",
        "delivery status of my order",

        # Damaged / Defective
        "defective product",
        "damaged item",
        "broken product",
        "faulty item",
        "i received a damaged product",
        "wrong item delivered",
        "my order is damaged",
        "product is not working",

        # Cancel
        "how to cancel my order",
        "cancel my order",
        "order cancellation process",
        "can i cancel after placing order",

        # Warranty
        "warranty policy",
        "product warranty",
        "guarantee on products",
        "replacement policy",
    ],
    score_threshold=0.25
)

# ─────────────────────────────────────────────
# 🔹 SQL ROUTE
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
        "show me laptops",
        "find me smartphones",
        "best headphones under 2000",
        "premium smartwatches",
        "budget friendly shoes",
        "show me samsung phones",
        "top rated earbuds",
    ],
    score_threshold=0.35
)

# ─────────────────────────────────────────────
# 🔹 SEMANTIC ROUTER
# ─────────────────────────────────────────────
router = SemanticRouter(
    routes=[faq, sql],
    encoder=encoder
)


# ─────────────────────────────────────────────
# 🔹 DB CHECK
# Checks if query words match real products
# in DB. Only runs when semantic is not confident.
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
# 🔹 INTENT CHECK
# Product not in DB but looks like a search.
# e.g. "show me gucci bags" → SQL
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
# 🔹 FAQ BACKUP CHECK
# Safety net for when semantic router fails
# or has low confidence. Catches clear FAQ
# queries using substring matching — not
# exact word matching so "money back process"
# and "track my product" are both caught.
# ─────────────────────────────────────────────
FAQ_BACKUP = [
    "track", "tracking", "refund", "return", "returning",
    "money back", "cancel", "cancellation", "warranty",
    "payment", "cod", "upi", "damaged", "defective",
    "broken", "wrong item", "complaint",
    "where is my order", "when will my order",
    "delivery status", "order status",
]

def is_faq_backup(query: str) -> bool:
    q = query.lower()
    return any(word in q for word in FAQ_BACKUP)


# ─────────────────────────────────────────────
# 🔹 FINAL ROUTE DETECTION
#
# Flow:
#   1. Semantic router (primary FAQ detector)
#   2. Confident FAQ → FAQ
#   3. FAQ backup → FAQ (when semantic fails)
#   4. DB check → SQL
#   5. Semantic low confidence FAQ → FAQ
#   6. Intent check → SQL
#   7. Default → FAQ
# ─────────────────────────────────────────────
def detect_route(query: str) -> str:
    query_lower = query.lower().strip()

    # Step 1: Semantic router — primary detector
    try:
        route = router(query_lower)
        semantic = route.name if route else None
        score = route.similarity_score if route else 0.0
    except Exception as e:
        print(f"[SEMANTIC ERROR] {e}")
        semantic = None
        score = 0.0

    print(f"[SEMANTIC] route={semantic}, score={score:.2f}")

    # Step 2: Confident FAQ from semantic router
    # Handles "track my product", "money back process" etc.
    if semantic == "faq" and score >= 0.4:
        return "faq"

    # Step 3: FAQ backup — runs when semantic fails or low confidence
    # Catches clear FAQ queries that slipped through
    if is_faq_backup(query_lower):
        return "faq"

    # Step 4: DB check — reliable product detection
    if is_product_query(query_lower):
        return "sql"

    # Step 5: Semantic said FAQ but low confidence → still FAQ
    if semantic == "faq":
        return "faq"

    # Step 6: Intent check — product not in DB
    if is_product_intent(query_lower):
        return "sql"

    # Step 7: Safe default
    return "faq"


# ─────────────────────────────────────────────
# 🔹 TEST
# ─────────────────────────────────────────────
if __name__ == '__main__':
    queries = [
        # ── Should go to SQL ──
        "premium smartwatches",
        "NOVA hair dryer",
        "show me 10 laptops",
        "budget friendly headphones",
        "top rated samsung phones",
        "show me gucci bags",
        "affordable shoes under 1000",
        "heavily discounted TVs",

        # ── Should go to FAQ ──
        "what is your return policy",
        "do you support COD",
        "how long does refund take",
        "track my order",
        "how to track my product",
        "how can i track my product",
        "what is money back process",
        "i received a damaged product",
        "how to return my item",
        "cancel my order",
        "when will my order arrive",
    ]

    print(f"{'Query':<45} {'Route'}")
    print("-" * 55)
    for q in queries:
        print(f"{q:<45} → {detect_route(q)}")