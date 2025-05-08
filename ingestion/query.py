import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

# Initialize OpenAI and Pinecone
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("cheese-products")
namespace = "cheese"

def embed_query(query: str):
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding failed: {e}")
        return None

def search(query_text: str, top_k=5):
    query_vector = embed_query(query_text)
    if not query_vector:
        return []

    try:
        result = index.query(
            namespace=namespace,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
        return result.get("matches", [])
    except Exception as e:
        print(f"Query failed: {e}")
        return []

def display_results(matches):
    print("\nTop Matching Cheeses:\n" + "-"*60)
    for i, match in enumerate(matches, 1):
        meta = match['metadata']
        print(f"{i}. {meta['title']}")
        print(f"   Brand: {meta.get('brand')}")
        print(f"   Price: {meta.get('price')}")
        print(f"   Link:  {meta.get('url')}")
        print(f"   Image: {meta.get('image_url')}\n")

if __name__ == "__main__":
    query = input("🔍 Enter your cheese query (e.g., 'cheap mozzarella under $30'): ")
    matches = search(query)
    display_results(matches)
