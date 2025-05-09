import os
import json
import uuid
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cheese_raw.json")
DOCS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cheese_docs.jsonl")

client = OpenAI(api_key=OPENAI_API_KEY)

### 🔍 GPT-driven enrichment
def enrich_text_with_gpt(product):
    prompt = f"""
Write a 2-3 sentence product summary suitable for a cheese recommendation chatbot.

Include brand, product type, and a helpful suggestion for how this cheese might be used. Be helpful, friendly, and accurate.

Product info:
- Name: {product.get('name', 'N/A')}
- Price: {product.get('prices', {}).get('Each', 'N/A')} ({product.get('pricePer', '')})
- Brand: {product.get('brand', '')}
- Department: {product.get('department', '')}
    """.strip()

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ GPT enrichment failed: {e}")
        return None

### 📝 Build and save enriched docs.jsonl
def generate_docs_jsonl():
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw_products = json.load(f)

    with open(DOCS_PATH, "w", encoding="utf-8") as out:
        for product in tqdm(raw_products, desc="Enriching with GPT"):
            text = enrich_text_with_gpt(product)
            if text:
                out.write(json.dumps({
                    "title": product.get("name", ""),
                    "text": text,
                    "price": product.get('prices', {}).get('Each', ''),
                    "brand": product.get("brand", ""),
                    "category": product.get("department", ""),
                    "product_url": product.get("href", ""),
                    "image_url": product.get("showImage", "")
                }) + "\n")

### 📦 Load enriched docs
def load_docs():
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if "text" in line]

### 🔢 Embedding function
def embed_text(text):
    resp = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return resp.data[0].embedding

### 🚀 Main routine
def main():
    generate_docs_jsonl()
    docs = load_docs()

    pc = Pinecone(api_key=PINECONE_API_KEY)
    if "cheese-products" not in pc.list_indexes().names():
        pc.create_index(
            name="cheese-products",
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    index = pc.Index("cheese-products")

    vectors = []
    for doc in tqdm(docs, desc="Embedding enriched docs"):
        try:
            emb = embed_text(doc["text"])
            vectors.append({
                "id": str(uuid.uuid4()),
                "values": emb,
                "metadata": doc
            })
        except Exception as e:
            print(f"❌ Failed to embed {doc['title']}: {e}")

    if vectors:
        index.upsert(vectors=vectors, namespace="cheese")
        print(f"✅ {len(vectors)} enriched vectors upserted to Pinecone.")
    else:
        print("⚠️ No vectors ingested.")


if __name__ == "__main__":
    main()
