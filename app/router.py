import sqlite3
from pathlib import Path
from semantic_router import Route, RouteLayer as SemanticRouter
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
# Safety net when semantic router fails.
# Uses substring matching for flexibility.
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
# 🔹 SAFE SEMANTIC CALL
# Returns (route_name, score) safely.
# Handles all possible return types from
# different versions of semantic-router.
# ─────────────────────────────────────────────
def get_semantic_result(query: str):
    try:
        route = router(query)
        if route is None:
            return None, 0.0

        name = route.name if hasattr(route, 'name') else None

        # Safely extract score — different versions return different types
        raw_score = None
        if hasattr(route, 'similarity_score'):
            raw_score = route.similarity_score
        elif hasattr(route, 'score'):
            raw_score = route.score

        # Convert to float safely
        if raw_score is None:
            score = 0.0
        elif isinstance(raw_score, (list, tuple)):
            score = float(raw_score[0]) if raw_score else 0.0
        else:
            score = float(raw_score)

        return name, score

    except Exception as e:
        print(f"[SEMANTIC ERROR] {e}")
        return None, 0.0


# ─────────────────────────────────────────────
# 🔹 FINAL ROUTE DETECTION
#
# Flow:
#   1. Semantic router → confident FAQ → FAQ
#   2. FAQ backup → FAQ (safety net)
#   3. DB check → SQL
#   4. Semantic low confidence FAQ → FAQ
#   5. Intent check → SQL
#   6. Default → FAQ
# ─────────────────────────────────────────────
def detect_route(query: str) -> str:
    query_lower = query.lower().strip()

    # Step 1: Semantic router
    semantic, score = get_semantic_result(query_lower)

    # Step 2: Confident FAQ from semantic
    if semantic == "faq" and score >= 0.4:
        return "faq"

    # Step 3: FAQ backup — when semantic fails or low confidence
    if is_faq_backup(query_lower):
        return "faq"

    # Step 4: DB check
    if is_product_query(query_lower):
        return "sql"

    # Step 5: Semantic said FAQ but low confidence
    if semantic == "faq":
        return "faq"

    # Step 6: Intent check
    if is_product_intent(query_lower):
        return "sql"

    # Step 7: Default
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