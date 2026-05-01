from semantic_router import Route, SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

# -----------------------------
# Encoder
# -----------------------------
encoder = HuggingFaceEncoder(
    name='sentence-transformers/all-MiniLM-L6-v2'
)

# -----------------------------
# FAQ Route (UNCHANGED)
# -----------------------------
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

# -----------------------------
# SQL Route (IMPROVED SLIGHTLY)
# -----------------------------
sql = Route(
    name='sql',
    utterances=[
        "show me products",
        "find products",
        "search for items",
        "browse products",

        "products under 5000",
        "items under budget",
        "products in price range",
        "filter products by price",
        "cheap products",
        "expensive items",

        "top rated products",
        "best products",
        "recommended items",
        "popular products",
        "top items",

        "buy product",
        "product price",
        "available products",
        "product details",

        # 🔥 added for short queries
        "items available",
        "products available"
    ],
    score_threshold=0.35
)

# -----------------------------
# Router
# -----------------------------
router = SemanticRouter(
    routes=[faq, sql],
    encoder=encoder,
    auto_sync="local"
)

# -----------------------------
# Keyword scoring (word-based)
# -----------------------------
def keyword_scores(query: str):
    words = query.split()

    product_keywords = [
        "buy", "show", "find", "search", "price", "under",
        "top", "best", "cheap", "products", "items",
        "recommend", "popular", "available", "stock"
    ]

    faq_keywords = [
        "return", "refund", "policy", "track", "payment",
        "damage", "defective"
    ]

    product_score = sum(word in words for word in product_keywords)
    faq_score = sum(word in words for word in faq_keywords)

    return product_score, faq_score


# -----------------------------
# Final Route Detection (BALANCED)
# -----------------------------
def detect_route(query: str):
    query_lower = query.lower()

    # 🔹 Step 1: semantic result
    route = router(query_lower)
    semantic = route.name if route else None

    # 🔹 Step 2: keyword scores
    product_score, faq_score = keyword_scores(query_lower)

    # -----------------------------
    # 🔥 Combined decision logic
    # -----------------------------

    # Strong semantic + aligned keywords
    if semantic == "faq" and faq_score >= product_score:
        return "faq"

    if semantic == "sql" and product_score >= faq_score:
        return "sql"

    # Keyword leaning
    if product_score > faq_score:
        return "sql"

    if faq_score > product_score:
        return "faq"

    # fallback to semantic
    if semantic:
        return semantic

    return "faq"


# -----------------------------
# Testing
# -----------------------------
if __name__ == '__main__':
    queries = [
        "What is your return policy?",
        "Do you support COD?",
        "show me top rated headphones",
        "products under 5000",
        "refund time",
        "show me chargers where return is available",
        "is return covered under damage policy?",
        "headphones available"
    ]

    for q in queries:
        print(q, "→", detect_route(q))