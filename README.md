# 🛍️ E-commerce Chatbot (LLM + SQL + RAG)

An intelligent e-commerce assistant that understands natural language queries and retrieves accurate results using a hybrid system combining **LLM-powered SQL generation** and **RAG-based FAQ retrieval**.

---

## 🚀 Links

🔗 **GitHub:** https://github.com/YOUR_USERNAME/YOUR_REPO
🌐 **Live Demo:** https://YOUR_PROJECT_LINK
👩‍💼 **LinkedIn:** https://linkedin.com/in/YOUR_PROFILE

---

## 📌 Overview

* Handles **product queries** (e.g., *“budget headphones under 2000”*)
* Handles **FAQ queries** (e.g., *“return policy”*)
* Uses hybrid architecture:

  * FAQ → **RAG (ChromaDB + embeddings)**
  * Products → **SQL (LLM + SQLite)**

---

## 🏗️ Architecture

```text
User Query
   ↓
Hybrid Router (semantic + keyword)
   ↓
FAQ (RAG)        Product Search (SQL + LLM)
   ↓                    ↓
ChromaDB          Preprocessing + Hints
                   ↓
                LLM → SQL
                   ↓
                SQLite DB
                   ↓
                Fallback Search
                   ↓
                Final Response
```

---

## ⚙️ Key Features

* 🔹 Hybrid routing (semantic + keyword)
* 🔹 RAG-based FAQ answering
* 🔹 LLM → SQL query generation
* 🔹 Query preprocessing:

  * `50k → 50000`
  * category mapping (phones → smartphones)
  * adjective → SQL (budget, top rated, etc.)
* 🔹 Robust fallback search (title + category + brand)
* 🔹 Safe SQL execution (SELECT-only)
* 🔹 Dynamic LIMIT handling
* 🔹 Clean product output (price, rating, link)

---

## 📸 Screenshots

### 💬 Chat Interface

![Chat UI](assets/screenshot1.png)

### 🛒 Product Results

![Product Results](assets/screenshot2.png)

---

## 🛠️ Tech Stack

* Python, Streamlit
* Groq LLM
* SQLite
* ChromaDB
* Sentence Transformers

---

## 🚀 Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO
cd YOUR_REPO

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt
streamlit run main.py
```

---

## 🎯 Key Highlight

> Hybrid system combining rule-based preprocessing, LLM-driven SQL generation, and fallback retrieval to ensure reliable product search on real-world data.

---

## 👩‍💻 Author

**Aditi Patil**
🔗 https://www.linkedin.com/in/aditi-patil31/
💻 https://github.com/AditiPatil31

---

⭐ If you like this project, consider giving it a star!
