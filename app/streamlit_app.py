import streamlit as st
from rag_chain import CheeseRAGChain
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = CheeseRAGChain()

# Set page config
st.set_page_config(
    page_title="Cheese Expert Chatbot",
    page_icon="🧀",
    layout="wide"
)

# Custom CSS for layout and product cards
st.markdown("""
<style>
    .product-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
    }
    .product-card {
        flex: 1 1 300px;
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .product-card img {
        width: 100%;
        max-height: 180px;
        object-fit: contain;
        margin-bottom: 10px;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🧀 Cheese Expert Chatbot")
st.markdown("Ask me anything about cheese products from Kimelo's website!")

# Chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "context" in message:
            with st.expander("🧾 View Reference Products"):
                st.markdown('<div class="product-grid">', unsafe_allow_html=True)
                for product in message["context"]:
                    st.markdown(f"""
                    <div class="product-card">
                        <img src="{product['image_url']}" alt="Product image" />
                        <h4>{product['title']}</h4>
                        <p>Price: {product['price']}</p>
                        <p>Brand: {product['brand']}</p>
                        <a href="{product['product_url']}" target="_blank">🔗 View Product</a>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

# Chat input
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

            with st.expander("🧾 View Reference Products"):
                st.markdown('<div class="product-grid">', unsafe_allow_html=True)
                for product in response["context"]:
                    st.markdown(f"""
                    <div class="product-card">
                        <img src="{product['image_url']}" alt="Product image" />
                        <h4>{product['title']}</h4>
                        <p>Price: {product['price']}</p>
                        <p>Brand: {product['brand']}</p>
                        <a href="{product['product_url']}" target="_blank">🔗 View Product</a>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response["response"],
        "context": response["context"]
    })
