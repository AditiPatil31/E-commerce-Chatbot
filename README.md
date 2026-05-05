# 🛍️ E-Commerce AI Chatbot

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=28&pause=1000&color=F97316&center=true&vCenter=true&width=600&lines=E-Commerce+AI+Chatbot;Natural+Language+to+SQL+to+Results;Intelligent+Hybrid+Routing+System" />

<br/>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge\&logo=streamlit\&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge\&logo=sqlite\&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F97316?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG-8B5CF6?style=for-the-badge)

<br/>

### 🔗 Connect & Explore

[![GitHub](https://img.shields.io/badge/GitHub-AditiPatil31-181717?style=for-the-badge\&logo=github)](https://github.com/AditiPatil31)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Aditi_Patil-0A66C2?style=for-the-badge\&logo=linkedin)](https://www.linkedin.com/in/aditi-patil31/)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Click_Here-F97316?style=for-the-badge)](https://aditi-ecommerce-ai-chatbot.streamlit.app/)

<br/>

> **Ask anything. Get real products. Instantly.**
> *Hybrid LLM + SQL + RAG powered shopping assistant*

</div>

---

## 🧠 What Makes This Different?

Most chatbots rely on either **RAG** (for FAQs) or **SQL** (for product retrieval).

This project combines both using an **intelligent routing layer** that understands user intent before deciding how to answer.

| Query Type      | Example                    | Handled By             |
| --------------- | -------------------------- | ---------------------- |
| Product Search  | "budget laptops under 40k" | LLM → SQL → SQLite     |
| FAQ             | "What is return policy?"   | RAG → ChromaDB         |
| Mixed Query     | "how to track my product"  | FAQ (correctly routed) |
| Unknown Product | "show me gucci bags"       | SQL fallback           |

---

## 🧠 Intelligent Routing System

Instead of relying on a single method, the chatbot uses a **layered decision system** to reduce errors and improve accuracy.

```
User Query
   ↓
Semantic Understanding
   ↓
FAQ Safety Check
   ↓
Database Matching
   ↓
Intent Detection
   ↓
Final Route → FAQ or SQL
```

### How it works

* The system first tries to **understand the meaning** of the query using a semantic model
* If the query clearly looks like a support/FAQ question, it is handled by the **RAG pipeline**
* If not, it checks whether the query matches **real products in the database**
* If no match is found, it falls back to **intent detection** to still handle shopping queries

This layered approach helps handle tricky cases like:

* "how to track my product" → correctly treated as FAQ
* "show me gucci bags" → treated as product search even if not in database

---

## 🏗️ Architecture

```
User Query
   ↓
Hybrid Router (semantic + DB + intent)
   ↓
FAQ (RAG)        Product Search (SQL + LLM)
   ↓                    ↓
ChromaDB          Query Preprocessing
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

* 🔹 Intelligent hybrid routing system
* 🔹 Handles **ambiguous and mixed queries reliably**
* 🔹 RAG-based FAQ answering (ChromaDB)
* 🔹 LLM-powered SQL generation
* 🔹 Database-driven product detection (no hardcoding)
* 🔹 Smart query preprocessing:

  * `50k → 50000`
  * category mapping (phones → smartphones)
  * adjective → SQL hints
* 🔹 Robust fallback search (title + brand + category)
* 🔹 Safe SQL execution (SELECT-only)
* 🔹 Dynamic LIMIT handling
* 🔹 Clean product output with links

---

## 📸 Screenshots

### 💬 Chat Interface

![Chat UI](assets/screenshot_1.png)

### 🛒 Product Results

![Product Results](assets/screenshot_2.png)

---

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **LLM:** Groq (LLaMA3)
* **Database:** SQLite
* **Vector DB:** ChromaDB
* **Embeddings:** Sentence Transformers
* **Language:** Python

---

## 🚀 Run Locally

```bash
git clone https://github.com/AditiPatil31/YOUR_REPO
cd YOUR_REPO

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
streamlit run main.py
```

---

## 🎯 Sample Queries

```
show me budget friendly headphones
top rated samsung phones under 20000
popular smartwatches
NOVA hair dryer
heavily discounted TVs

how to track my order
money back process
cancel my order
```

---

## 📌 Why This Project Stands Out

* Combines **semantic understanding + rule-based safety + database grounding**
* Reduces common chatbot failures (wrong routing, mixed queries)
* Automatically adapts to **new products added to the database**
* Designed with **real-world edge cases in mind**

---

<div align="center">

## 👩‍💻 Author

**Aditi Patil**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge\&logo=linkedin\&logoColor=white)](https://www.linkedin.com/in/aditi-patil31/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge\&logo=github\&logoColor=white)](https://github.com/AditiPatil31)

<br/>

⭐ **If you like this project, consider giving it a star!**

</div>
