<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=28&pause=1000&color=F97316&center=true&vCenter=true&width=600&lines=🛍️+E-Commerce+AI+Chatbot;Natural+Language+→+SQL+→+Results;6,795+Products+%7C+90%2B+Categories" />

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
[![Live Demo](https://img.shields.io/badge/Live_Demo-Click_Here-F97316?style=for-the-badge)](https://YOUR_PROJECT_LINK)

<br/>

> **Ask anything. Get real products. Instantly.**
> *Hybrid LLM + SQL + RAG powered shopping assistant*

</div>

---

## 🧠 What Makes This Different?

Most chatbots use either **RAG** or **SQL**.
This project combines both using a **hybrid routing system**:

| Query Type      | Example                    | Handled By                 |
| --------------- | -------------------------- | -------------------------- |
| Product Search  | "budget laptops under 40k" | LLM → SQL → SQLite         |
| FAQ             | "What is return policy?"   | RAG → ChromaDB             |
| Brand + Product | "NOVA hair dryer"          | SQL (brand + title search) |
| Color + Product | "pink hair dryer"          | SQL multi-match            |
| Adjective Query | "premium smartwatch"       | SQL hints                  |

---

## 🏗️ Architecture

```
User Query
   ↓
Hybrid Router (semantic + keyword)
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

## 📸 Screenshots

### 💬 Chat Interface

![Chat UI](assets/screenshot1.png)

### 🛒 Product Results

![Product Results](assets/screenshot2.png)

---

## ⚙️ Key Features

* 🔹 Hybrid routing (semantic + keyword)
* 🔹 RAG-based FAQ answering
* 🔹 LLM-powered SQL generation
* 🔹 Smart query preprocessing:

  * `50k → 50000`
  * category mapping (phones → smartphones)
  * adjective → SQL hints
* 🔹 Fallback search for robustness
* 🔹 Safe SQL execution (SELECT-only)
* 🔹 Dynamic LIMIT handling
* 🔹 Clean product output with links

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
venv\Scripts\activate   # Windows

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
show me 10 laptops
what is the return policy?
```

---

<div align="center">

## 👩‍💻 Author

**Aditi Patil**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge\&logo=linkedin\&logoColor=white)](https://www.linkedin.com/in/aditi-patil31/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge\&logo=github\&logoColor=white)](https://github.com/AditiPatil31)

<br/>

⭐ **If you like this project, consider giving it a star!**

</div>
