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

data_path = os.path.join(os.path.dirname(__file__), "..", "data", "cheese_raw.json")

client = OpenAI(api_key=OPENAI_API_KEY)

def load_data():
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

def embed_text(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def build_text(product):
    return f"{product['title']} - {product.get('brand', '')}\nPrice: {product['price']}\nCategory: {product.get('category', '')}"

def main():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    if "cheese-products" not in pc.list_indexes().names():
        pc.create_index(
            name="cheese-products",
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    index = pc.Index("cheese-products")

    products = load_data()
    print(f"📦 Loaded {len(products)} products")

    vectors = []
    for product in tqdm(products, desc="Embedding products"):
        try:
            text = build_text(product)
            embedding = embed_text(text)
            vectors.append({
                "id": str(uuid.uuid4()),
                "values": embedding,
                "metadata": {
                    "text": text,
                    "title": product["title"],
                    "price": product["price"],
                    "brand": product.get("brand", ""),
                    "category": product.get("category", ""),
                    "url": product.get("product_url", ""),
                    "image_url": product.get("image_url", "")
                }
            })
        except Exception as e:
            print(f"❌ Embedding failed: {e}")

    if vectors:
        index.upsert(vectors=vectors, namespace="cheese")
        print(f"✅ Ingested {len(vectors)} vectors to Pinecone.")
    else:
        print("⚠️ No vectors were ingested.")

if __name__ == "__main__":
    main()
