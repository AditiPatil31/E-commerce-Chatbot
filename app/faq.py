import os
import pandas as pd
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
import re
import streamlit as st

# ─────────────────────────────────────────────
# 🔹 LOAD API KEYS
# Works on both local (.env) and Streamlit Cloud (secrets)
# ─────────────────────────────────────────────

# Try Streamlit secrets first (Streamlit Cloud)
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", None)
GROQ_MODEL = st.secrets.get("GROQ_MODEL", None)




# Fallback to .env for local development
if not GROQ_API_KEY:
    from dotenv import load_dotenv
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL")

# Final check — fail early with clear message
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Add it in Streamlit secrets or .env file.")
if not GROQ_MODEL:
    raise ValueError("GROQ_MODEL not found. Add it in Streamlit secrets or .env file.")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────────
# 🔹 PATHS
# ─────────────────────────────────────────────
faqs_path = Path(__file__).parent / "resources/faq_data.csv"

# ─────────────────────────────────────────────
# 🔹 EMBEDDING + CHROMA SETUP
# ─────────────────────────────────────────────
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name='sentence-transformers/all-MiniLM-L6-v2'
)

chroma_client = chromadb.Client()
collection_name_faq = 'faqs'

# ─────────────────────────────────────────────
# 🔹 INGEST FAQ DATA
# ─────────────────────────────────────────────
def ingest_faq_data(path):
    if collection_name_faq not in [c.name for c in chroma_client.list_collections()]:
        print("Ingesting FAQ data into ChromaDB...")
        collection = chroma_client.create_collection(
            name=collection_name_faq,
            embedding_function=ef
        )

        df = pd.read_csv(path)
        docs = df['question'].to_list()
        metadata = [{'answer': ans} for ans in df['answer'].to_list()]
        ids = [f"id_{i}" for i in range(len(docs))]

        collection.add(
            documents=docs,
            metadatas=metadata,
            ids=ids
        )

        print(f"FAQ Data ingested into collection: {collection_name_faq}")
    else:
        print(f"Collection already exists: {collection_name_faq}")

# ─────────────────────────────────────────────
# 🔹 QUERY EXPANSION
# ─────────────────────────────────────────────
ABBREVIATION_MAP = {
    "cod": "cash on delivery",
    "upi": "unified payments interface",
    "cc": "credit card",
    "dc": "debit card",
    "emi": "equated monthly installment",
    "faq": "frequently asked questions",
    "tnc": "terms and conditions"
}

def expand_query(query: str) -> str:
    words = re.findall(r'\b\w+\b', query.lower())
    expanded_words = []
    for word in words:
        expanded_words.append(word)
        if word in ABBREVIATION_MAP:
            expanded_words.append(ABBREVIATION_MAP[word])
    return " ".join(expanded_words)

# ─────────────────────────────────────────────
# 🔹 RETRIEVAL
# ─────────────────────────────────────────────
def get_relevant_qa(query):
    collection = chroma_client.get_collection(
        name=collection_name_faq,
        embedding_function=ef
    )
    result = collection.query(
        query_texts=[query],
        n_results=4
    )
    return result

def get_best_context(result):
    metadatas = result['metadatas'][0]
    distances = result['distances'][0]

    pairs = list(zip(metadatas, distances))
    pairs.sort(key=lambda x: x[1])

    top_answers = [p[0].get('answer') for p in pairs[:2] if p[0].get('answer')]

    return "\n".join(top_answers) if top_answers else "NO_CONTEXT"

# ─────────────────────────────────────────────
# 🔹 ANSWER GENERATION
# ─────────────────────────────────────────────
def generate_answer(query, context):
    prompt = f"""
You are an ecommerce FAQ assistant.

STRICT RULES:
1. Answer only from the context.
2. Rephrase if needed.
3. If answer not present → say "I don't know".
4. Keep it short.

CONTEXT:
{context}

QUESTION:
{query}
"""
    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a strict and truthful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    answer = completion.choices[0].message.content.strip()

    if not answer:
        return "I don't know."

    return answer

# ─────────────────────────────────────────────
# 🔹 MAIN FAQ PIPELINE
# ─────────────────────────────────────────────
def faq_chain(query):
    query = expand_query(query)

    result = get_relevant_qa(query)
    context = get_best_context(result)

    if context == "NO_CONTEXT":
        return "I don't have that information right now."

    print("Context:", context)

    answer = generate_answer(query, context)

    if "i don't know" in answer.lower():
        return "I don't have that information right now."

    return answer

# ─────────────────────────────────────────────
# 🔹 TEST
# ─────────────────────────────────────────────
if __name__ == '__main__':
    ingest_faq_data(faqs_path)

    query = "what are tnc for damaged product"
    answer = faq_chain(query)

    print("Answer:", answer)