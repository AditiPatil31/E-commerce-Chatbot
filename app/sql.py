from groq import Groq
import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = os.getenv('GROQ_MODEL')
db_path = Path(__file__).parent / "db.sqlite"
client_sql = Groq()


# ─────────────────────────────────────────────
# 🔹 ADJECTIVE MAP
# Translates natural language words → SQL hints
# NOTE: "premium" uses a moderate threshold (10000)
# because most products in DB are under 50000
# ─────────────────────────────────────────────

ADJECTIVE_MAP = {
    # Rating based
    "top rated":          "avg_rating >= 4.5 ORDER BY avg_rating DESC",
    "best rated":         "avg_rating >= 4.5 ORDER BY avg_rating DESC",
    "highly rated":       "avg_rating >= 4.0 ORDER BY avg_rating DESC",
    "popular":            "total_ratings >= 1000 ORDER BY total_ratings DESC",
    "well reviewed":      "avg_rating >= 4.0 ORDER BY avg_rating DESC",
    "good":               "avg_rating >= 4.0",

    # Price based
    "cheap":              "ORDER BY price ASC",
    "cheapest":           "ORDER BY price ASC",
    "affordable":         "price < 5000 ORDER BY price ASC",
    "budget":             "price < 5000 ORDER BY price ASC",
    "budget friendly":    "price < 5000 ORDER BY price ASC",
    "premium":            "ORDER BY price DESC",   # top priced in that category
    "expensive":          "ORDER BY price DESC",
    "high end":           "ORDER BY price DESC",

    # Discount based
    "discounted":         "discount > 0.2 ORDER BY discount DESC",
    "on sale":            "discount > 0.1 ORDER BY discount DESC",
    "best deal":          "discount > 0.2 ORDER BY discount DESC",
    "best deals":         "discount > 0.2 ORDER BY discount DESC",
    "heavily discounted": "discount > 0.4 ORDER BY discount DESC",
    "offers":             "discount > 0.1 ORDER BY discount DESC",
}

# ─────────────────────────────────────────────
# 🔹 CATEGORY MAP
# Maps user words → actual DB category names
# ─────────────────────────────────────────────

CATEGORY_MAP = {
    "tv":           "smart tv",
    "tvs":          "smart tv",
    "television":   "smart tv",
    "televisions":  "smart tv",
    "phone":        "smartphones",
    "phones":       "smartphones",
    "mobile":       "smartphones",
    "mobiles":      "smartphones",
    "headphone":    "bluetooth headphones",
    "headphones":   "bluetooth headphones",
    "earphone":     "neckband earphones",
    "earphones":    "neckband earphones",
    "earbud":       "wireless earbuds",
    "earbuds":      "wireless earbuds",
    "fridge":       "refrigerator double door",
    "ac":           "air conditioner split",
    "cooler":       "air conditioner split",
    "watch":        "smartwatch",
    "watches":      "smartwatch",
    "shoe":         "men casual shoes",
    "shoes":        "men casual shoes",
    "speaker":      "bluetooth speaker",
    "speakers":     "bluetooth speaker",
    "camera":       "dslr camera",
    "cameras":      "dslr camera",
    "book":         "self help books",
    "books":        "self help books",
}


# ─────────────────────────────────────────────
# 🔹 NORMALIZE USER INPUT
# 50k → 50000, tvs → smart tv etc.
# ─────────────────────────────────────────────

def normalize_query(question: str) -> str:
    q = question.lower().strip()
    q = re.sub(r'(\d+)\s*lakh', lambda m: str(int(m.group(1)) * 100000), q)
    q = re.sub(r'(\d+)\s*k\b',  lambda m: str(int(m.group(1)) * 1000), q)
    for alias, real in CATEGORY_MAP.items():
        q = re.sub(rf'\b{alias}\b', real, q)
    return q


# ─────────────────────────────────────────────
# 🔹 INJECT ADJECTIVE HINTS
# "budget friendly phones" →
# "budget friendly phones [HINTS: price < 5000 ORDER BY price ASC]"
# ─────────────────────────────────────────────

def inject_adjective_hints(question: str) -> str:
    hints = []
    q_lower = question.lower()
    for phrase, sql_hint in ADJECTIVE_MAP.items():
        if phrase in q_lower:
            hints.append(sql_hint)
    if hints:
        question += f" [HINTS: {' | '.join(hints)}]"
    return question


# ─────────────────────────────────────────────
# 🔹 SQL PROMPT
# ─────────────────────────────────────────────

sql_prompt = """You are a SQLite query generator for a Flipkart product database.

Table: product
Columns: product_link, title, brand, price, discount, avg_rating, total_ratings, category

Rules:
- Always SELECT *
- Default LIMIT 5 unless user asks for more
- Search title using: LOWER(title) LIKE '%keyword%'
- Search category using: LOWER(category) LIKE '%keyword%'

- For brand names (samsung, boat, realme, havells, rk etc.):
    Search BOTH title AND brand:
    WHERE (LOWER(title) LIKE '%samsung%' OR LOWER(brand) LIKE '%samsung%')

- IMPORTANT — For short brand names like "nova", "rk", "vega":
    Use word-boundary style: LOWER(brand) = 'nova' OR LOWER(brand) LIKE 'nova %'
    This avoids matching "supernova", "renovation" etc.

- For color + product (e.g. "pink hair dryer"):
    WHERE LOWER(title) LIKE '%pink%' AND LOWER(category) LIKE '%hair%'

- For brand + product (e.g. "NOVA hair dryer"):
    WHERE (LOWER(brand) = 'nova' OR LOWER(brand) LIKE 'nova %' OR LOWER(title) LIKE '%nova %') AND LOWER(category) LIKE '%hair%'

- price under X → price < X
- price above X → price > X
- top / best    → ORDER BY avg_rating DESC
- cheapest      → ORDER BY price ASC
- most popular  → ORDER BY total_ratings DESC
- premium / expensive / high end → ORDER BY price DESC (do NOT add price > X filter)
- If [HINTS: ...] provided, use them directly in the SQL

Examples:
  "show me iphones"
  → SELECT * FROM product WHERE LOWER(title) LIKE '%iphone%' OR LOWER(brand) LIKE '%apple%' LIMIT 5;

  "laptops under 50000"
  → SELECT * FROM product WHERE LOWER(category) LIKE '%laptop%' AND price < 50000 LIMIT 5;

  "NOVA hair dryer"
  → SELECT * FROM product WHERE (LOWER(brand) = 'nova' OR LOWER(brand) LIKE 'nova %' OR LOWER(title) LIKE '%nova %') AND LOWER(category) LIKE '%hair%' LIMIT 5;

  "havells hair dryer"
  → SELECT * FROM product WHERE (LOWER(title) LIKE '%havells%' OR LOWER(brand) LIKE '%havells%') AND LOWER(category) LIKE '%hair%' LIMIT 5;

  "rk india hair dryer"
  → SELECT * FROM product WHERE (LOWER(title) LIKE '%rk india%' OR LOWER(brand) LIKE '%rk%') AND LOWER(category) LIKE '%hair%' LIMIT 5;

  "premium smartwatches [HINTS: ORDER BY price DESC]"
  → SELECT * FROM product WHERE LOWER(category) LIKE '%smartwatch%' ORDER BY price DESC LIMIT 5;

  "boat earphones under 2000"
  → SELECT * FROM product WHERE (LOWER(title) LIKE '%boat%' OR LOWER(brand) LIKE '%boat%') AND price < 2000 LIMIT 5;

  "top rated samsung phones [HINTS: avg_rating >= 4.5 ORDER BY avg_rating DESC]"
  → SELECT * FROM product WHERE (LOWER(title) LIKE '%samsung%' OR LOWER(brand) LIKE '%samsung%') AND avg_rating >= 4.5 ORDER BY avg_rating DESC LIMIT 5;

Return ONLY the SQL query inside <SQL>...</SQL> tags. No explanation.
"""


# ─────────────────────────────────────────────
# 🔹 RESPONSE FORMAT PROMPT
# ─────────────────────────────────────────────

comprehension_prompt = """You are a helpful shopping assistant. Present the product data clearly.

Format each product as:
1. **Title** — ₹price (discount% off) | ⭐ rating | [View on Flipkart](link)

Rules:
- Show all products from the data
- If discount is None, skip the discount part
- If avg_rating is None, skip the rating part
- If no products, say "No products found matching your search."
- No extra explanation needed
"""


# ─────────────────────────────────────────────
# 🔹 GENERATE SQL USING LLM
# ─────────────────────────────────────────────

def generate_sql_query(question: str) -> str:
    response = client_sql.chat.completions.create(
        messages=[
            {"role": "system", "content": sql_prompt},
            {"role": "user", "content": question}
        ],
        model=GROQ_MODEL,
        temperature=0.1
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────
# 🔹 RUN SQL QUERY
# ─────────────────────────────────────────────

def run_query(query: str) -> pd.DataFrame | None:
    query = query.strip()
    if not query.lower().startswith("select"):
        print(f"[WARN] Non-SELECT query blocked: {query}")
        return None
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
            return df
    except Exception as e:
        print(f"[SQL ERROR] {e}\nQuery: {query}")
        return None


# ─────────────────────────────────────────────
# 🔹 FALLBACK SEARCH
# Used when LLM query returns empty results.
# Uses AND logic — all keywords must match.
# Searches title + brand + category columns.
# ─────────────────────────────────────────────

NOISE_WORDS = {
    "show", "me", "give", "list", "find", "get", "search",
    "products", "items", "product", "item", "some", "any", "all",
    "under", "above", "below", "between", "and", "with", "a", "an", "the",
    "best", "top", "cheap", "cheapest", "good", "great", "budget", "friendly",
    "rated", "rating", "popular", "rs", "inr", "rupees", "price", "premium",
    "affordable", "discounted", "highly", "well", "reviewed", "offers", "sale",
}

def fallback_search(question: str) -> pd.DataFrame | None:
    q = re.sub(r'\b\d[\d,]*\b', '', question.lower())
    keywords = [w for w in re.findall(r'[a-z]+', q)
                if w not in NOISE_WORDS and len(w) > 1]
    print(f"[FALLBACK] keywords: {keywords}")

    if not keywords:
        return None

    price_clause = ""
    price_match = re.search(r'under\s+(\d+)', question.lower())
    if price_match:
        price_clause = f"AND price < {price_match.group(1)}"

    # AND between keywords — all must match across title/brand/category
    conditions = " AND ".join(
        f"(LOWER(title) LIKE '%{kw}%' OR LOWER(brand) LIKE '%{kw}%' OR LOWER(category) LIKE '%{kw}%')"
        for kw in keywords
    )

    query = f"""
        SELECT * FROM product
        WHERE ({conditions})
        {price_clause}
        ORDER BY avg_rating DESC
        LIMIT 5
    """
    return run_query(query)


# ─────────────────────────────────────────────
# 🔹 FORMAT RESPONSE USING LLM
# ─────────────────────────────────────────────

def format_response(question: str, context: list[dict]) -> str:
    response = client_sql.chat.completions.create(
        messages=[
            {"role": "system", "content": comprehension_prompt},
            {"role": "user", "content": f"Question: {question}\n\nProduct Data:\n{context}"}
        ],
        model=GROQ_MODEL,
        temperature=0.2
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────
# 🔹 MAIN FUNCTION — called by your chatbot
# ─────────────────────────────────────────────

def sql_chain(question: str) -> str:

    # Step 1: Normalize (50k → 50000, tvs → smart tv etc.)
    normalized = normalize_query(question)
    print(f"[INPUT] {normalized}")

    # Step 2: Inject adjective hints (budget friendly → price < 5000 etc.)
    enriched = inject_adjective_hints(normalized)
    print(f"[ENRICHED] {enriched}")

    # Step 3: Generate SQL using LLM
    raw_response = generate_sql_query(enriched)
    match = re.findall(r"<SQL>(.*?)</SQL>", raw_response, re.DOTALL)
    sql_query = match[0].strip() if match else raw_response.strip()
    print(f"[SQL] {sql_query}")

    # Step 4: Run SQL
    df = run_query(sql_query)

    # Step 5: Fallback if empty
    if df is None or df.empty:
        print("[INFO] No results — trying fallback search...")
        df = fallback_search(normalized)

        if df is None or df.empty:
            return "Sorry, I couldn't find any matching products. Try rephrasing your search."

    # Step 6: Limit results
    limit_match = re.search(
        r'\b([1-9][0-9]?)\s*(?:products?|items?|laptops?|phones?|results?|watches?|shoes?)?\b',
        question.lower()
    )
    limit = int(limit_match.group(1)) if limit_match else 5
    df = df.head(limit)

    print(f"[RESULTS] {len(df)} products found")

    # Step 7: Format and return
    context = df.to_dict(orient='records')
    return format_response(question, context)


# ─────────────────────────────────────────────
# 🔹 TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        "show me budget friendly headphones",
        "top rated samsung phones",
        "popular smartwatches",
        "premium smartwatches",
        "heavily discounted TVs",
        "affordable shoes under 1000",
        "NOVA hair dryer",
        "havells hair dryer",
        "rk india hair dryer",
        "boat earphones under 2000",
        "show me 10 laptops",
    ]
    for q in tests:
        print(f"\n{'='*50}")
        print(f"Q: {q}")
        print(sql_chain(q))