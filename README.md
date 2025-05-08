# 🧀 Cheese RAG Chatbot

A RAG-powered chatbot that answers questions about cheese products using OpenAI GPT-4o and Pinecone Vector DB.

## 🔍 Features

- Web scraping of cheese products from Kimelo's website
- Vector database storage using Pinecone
- RAG-based question answering using OpenAI GPT-4
- Interactive chat interface built with Streamlit
- Context-aware responses with source references

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   ```

## Project Structure

```
cheese-rag-chatbot/
├── scraping/                  # Scraper script (Selenium)
├── data/                      # Raw and processed product data
├── ingestion/                # Embedding + Pinecone upsert logic
├── chatbot/                  # RAG logic and retriever chain
├── app/                      # Streamlit app UI
├── .streamlit/config.toml    # Streamlit theme
├── .env.example              # API key template (never commit .env)
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Run Locally

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/cheese-rag-chatbot.git
cd cheese-rag-chatbot
```

### 2. Set up environment

```bash
cp .env.example .env  # and fill in your real keys
pip install -r requirements.txt
```

### 3. Run the chatbot

```bash
streamlit run app/streamlit_app.py
```

---

## ☁️ Deploy on Streamlit Cloud

1. Push this repo to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your repo and set the main file to `app/streamlit_app.py`
4. Add environment secrets (OPENAI, PINECONE keys)
5. 🚀 Deploy

---

## 📦 Environment Variables

Place these in a `.env` file (not tracked by Git):

```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=your-region  # e.g. gcp-starter or us-east1-gcp
```

---

## 📝 License

MIT License © [John Hinton]
