# Cheese RAG Chatbot

A RAG-based chatbot that answers questions about cheese products from Kimelo's website.

## Features

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
│
├── scraping/
│   └── scraper.py           # Selenium script to scrape cheese product data
│
├── data/
│   └── cheese_raw.json      # Raw scraped data
│   └── cheese_docs.jsonl    # Cleaned, chunked documents with metadata
│
├── ingestion/
│   └── ingest.py            # Converts data to embeddings and uploads to Pinecone
│
├── chatbot/
│   └── rag_chain.py         # RAG pipeline: query -> retrieve -> generate
│
├── app/
│   └── streamlit_app.py     # Streamlit frontend with chat UI and streaming
│
├── requirements.txt
└── README.md
```

## Usage

1. Run the scraper to collect data:
   ```bash
   python scraping/scraper.py
   ```

2. Ingest the data into Pinecone:
   ```bash
   python ingestion/ingest.py
   ```

3. Launch the Streamlit app:
   ```bash
   streamlit run app/streamlit_app.py
   ```

## Deployment

The app is deployed on Streamlit Cloud and can be accessed at [your-streamlit-url].

## License

MIT