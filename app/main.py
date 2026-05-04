import streamlit as st
from faq import ingest_faq_data, faq_chain
from pathlib import Path
from router import detect_route
from sql import sql_chain

# -----------------------------
# Page Config (must be first Streamlit call)
# -----------------------------
st.set_page_config(
    page_title="E-commerce Bot",
    page_icon="🛍️",
    layout="centered"
)

# -----------------------------
# Setup (IMPORTANT FIX)
# Run ingestion only once using cache
# -----------------------------
faqs_path = Path(__file__).parent / "resources/faq_data.csv"

@st.cache_resource
def load_faq():
    ingest_faq_data(faqs_path)

load_faq()

# -----------------------------
# Custom Styling
# -----------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
h1 {
    text-align: center;
}
.tagline {
    text-align: center;
    color: grey;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Title + Tagline
# -----------------------------
st.title("🛍️ E-commerce Assistant")

st.markdown("""
<div style='text-align: center; 
            font-size: 20px; 
            color: #4CAF50; 
            font-weight: 600;
            margin-top: -10px;
            margin-bottom: 25px;'>
    ✨ Your shopping assistant, ready when you are.
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("⚙️ Controls")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# -----------------------------
# Router Logic
# -----------------------------
def ask(query):
    route = detect_route(query)
    print("Detected Route:", route)

    try:
        if route == "faq":
            return faq_chain(query)

        elif route == "sql":
            return sql_chain(query)

        else:
            return faq_chain(query)

    except Exception as e:
        print("ERROR:", e)
        return "Something went wrong. Please try again."

# -----------------------------
# Chat History
# -----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# -----------------------------
# Input
# -----------------------------
query = st.chat_input("Ask about products, orders, returns, payments...")

if query:
    # User message
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    # Bot response
    response = ask(query)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})