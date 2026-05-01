import os
import pandas as pd
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
import re


from dotenv import load_dotenv

load_dotenv()

faqs_path = Path(__file__).parent / "resources/faq_data.csv"

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name='sentence-transformers/all-MiniLM-L6-v2'
        )

chroma_client = chromadb.Client()
groq_client = Groq()
collection_name_faq = 'faqs'


def ingest_faq_data(path):
    if collection_name_faq not in [c.name for c in chroma_client.list_collections()]:
        print("Ingesting FAQ data into Chromadb...")
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
        print(f"FAQ Data successfully ingested into Chroma collection: {collection_name_faq}")
    else:
        print(f"Collection: {collection_name_faq} already exist")

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
    pairs.sort(key=lambda x: x[1])  # smaller distance = more relevant

    top_answers = [p[0].get('answer') for p in pairs[:2] if p[0].get('answer')]

    return "\n".join(top_answers) if top_answers else "NO_CONTEXT"





def generate_answer(query, context):
    prompt = f""" 
                You are an ecommerce FAQ assistant.

                STRICT RULES:
                  1. Answer based on the provided context.
                  2. You can rephrase or interpret the meaning of the context.
                  3. If the answer is not present at all, say "I don't know".
                  4. Keep the answer short and precise.


          CONTEXT:
          {context}

          QUESTION:
         {query}
        """

    completion = groq_client.chat.completions.create(
        model=os.environ['GROQ_MODEL'],
        messages=[# type: ignore
            {"role": "system", "content": "You are a strict and truthful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0  # 🔥 important for consistency
    )

    answer = completion.choices[0].message.content.strip()

    # 🔒 Guardrail 3: Output validation
    if not answer:
        return "I don't know."

    return answer

def faq_chain(query):
    query = expand_query(query)

    result = get_relevant_qa(query)

    # ✅ use filtered context instead of all results
    context = get_best_context(result)

    # 🔒 Guardrail: No relevant data
    if context == "NO_CONTEXT":
        return "I don’t have that information right now."

    print("Context:", context)

    answer = generate_answer(query, context)

    # 🔒 Guardrail: fallback check
    if "i don't know" in answer.lower():
        return "I don’t have that information right now."

    return answer





if __name__ == '__main__':
    ingest_faq_data(faqs_path)
    query = ("what are tnc for damaged product"
             "")
    answer = faq_chain(query)
    print("Answer:",answer)