import streamlit as st
from rag_chain import CheeseRAGChain
from PIL import Image
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = CheeseRAGChain()
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

favicon = Image.open("mark.png")
st.set_page_config(page_title="Kilmeo's Cheese Expert Chatbot", page_icon=favicon, layout="wide")

# Theme toggle
st.sidebar.markdown("## Theme")
theme = st.sidebar.radio("Choose theme", options=["dark", "light"], index=0, horizontal=True)
st.session_state.theme = theme

# Theme styling
if theme == "dark":
    st.markdown("""
    <style>
        .stApp, .block-container { background-color: #1f1f2e; color: #f0f0f0; }
        h1, h2, h3, h4, h5, h6, p, span { color: #f0f0f0 !important; }
        .product-card { background-color: #2c2c3a; color: #f0f0f0; }
        .product-title { color: #f1f1f1; }
        .product-meta { color: #ccc; }
        .price-tag { color: #ffdf91; }
        .price-unit { color: #aaa; }
        .product-link { color: #9ecbff; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp, .block-container { background-color: #fefefe; color: #111; }
        h1, h2, h3, h4, h5, h6, p, span { color: #111 !important; }
        .product-card { background-color: #f9f9f9; color: #222; }
        .product-title { color: #111; }
        .product-meta { color: #444; }
        .price-tag { color: #c04f00; }
        .price-unit { color: #666; }
        .product-link { color: #1a73e8; }
    </style>
    """, unsafe_allow_html=True)

# Header section with logo
col1, col2 = st.columns([1, 5])
with col1:
    st.image("mark.png", width=100)
with col2:
    st.title("Kilmeo's Cheese Expert Chatbot")
    st.markdown(
        "I am an online assistant specializing in cheese products available on shop.kimelo.com."
        " I can provide information about the vast variety of cheeses offered on the site, including types, brands, and prices. I am here to assist with any questions you may have about the cheese products on the site."
    )

# Card renderer with fallback image
def render_product(product):
    image_url = product.get("image_url") or "https://via.placeholder.com/250x180?text=No+Image"
    return f"""
    <div class='product-card' style='flex: 0 0 auto; width: 260px; border-radius: 0.75rem; padding: 1rem; margin-bottom: 1rem;
         box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-right: 12px;'>
        <img src='{image_url}' alt='Product image' style='width: 100%; height: 180px; object-fit: contain;
             border-radius: 0.5rem; margin-bottom: 10px;' />
        <div class='product-title'><strong>{product["title"]}</strong></div>
        <div class='product-meta'><strong>Brand:</strong> {product.get("brand", "N/A")}</div>
        <div class='product-meta'><strong>Category:</strong> {product.get("category", "N/A")}</div>
        <div class='price-tag'>{product.get("price", "")} <span class='price-unit'>{product.get("price_per_unit", "")}</span></div>
        <a href='{product["product_url"]}' target='_blank' class='product-link'>🔗 View Product</a>
    </div>
    """

# Horizontal scroll layout
def display_products(products):
    st.markdown('<div class="product-scroll" style="display: flex; overflow-x: auto; padding: 0 4px 12px 0;">',
                unsafe_allow_html=True)
    for product in products:
        st.markdown(render_product(product), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Chat history display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "context" in message:
            with st.expander("🧾 View Reference Products"):
                display_products(message["context"])

# Input logic
if prompt := st.chat_input("Ask a question about cheese..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.rag_chain.generate_response(prompt)
            full_response = ""
            message_placeholder = st.empty()
            for chunk in response["response"].split():
                full_response += chunk + " "
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            # with st.expander("🧀 Cheeses You Might Like"):
            #     display_products(response["context"])
    st.session_state.messages.append({
        "role": "assistant",
        "content": response["response"],
        "context": response["context"]
    })