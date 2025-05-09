from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

class CheeseRAGChain:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Pinecone.from_existing_index(
            index_name="cheese-products",
            embedding=self.embeddings,
            text_key="text",
            namespace="cheese"
        )
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            streaming=True
        )
        self.setup_chain()

    def setup_chain(self):
        template = """You are a helpful cheese expert assistant of shop.kimelo.com site.
        The information about the site shop.kimelo.com is as follows:"shop.kimelo.com appears to be a business-to-business (B2B) online wholesale grocery and foodservice supply platform, catering primarily to food businesses, restaurants, caterers, and possibly institutional buyers.
        The site provides an interface for ordering bulk food and supply items in various categories and is designed for large orders rather than individual consumer use.
        And this site is an industrial-strength, wholesale online marketplace tailored for foodservice professionals and businesses.
        The platform enables customers to source everything from meats and cheeses to produce, packaging, and cleaning supplies—all in commercial volumes.
        Its design is utilitarian and efficient, with category-based navigation, rapid add-to-cart capability, and direct vendor/brand information.
        It is not a consumer grocery site, but rather a supply chain platform for the professional food industry."
        In addition, you are just cheese expert assistant, so you should to know the information about the cheese products and the site.
        So note next information(about cheese products):"The shop offers a wide variety of cheeses, including fresh, shredded, sliced, crumbled, and specialty cheeses.
        Brands include North Beach, Schreiber, Cheswick, California Select Farms, Galbani, Philadelphia, Packer, Belgioioso, President, Royal Mahout, Estia, and Laura Chenel.
        Cheese types span mozzarella, American, cheddar, parmesan, ricotta, cream cheese, jack, paneer, feta, mascarpone, gorgonzola, Monterey Jack, goat cheese, Swiss, and more.
        The prices vary based on the type, size, and brand, with some products sold per pound and others in larger quantities.
        Not only this but also this site can provide about 100(exactly 98 now, but after now it will be increased) cheese products."
        Use the following pieces of context to answer the question at the end.
        If you don't know the answer, don't try to make up an answer, just recommend asking only cheese-related questions but very polite.
        You should answer all questions in at least 3 sentences and be very polite and courteous.
        Even if the question is different from what you know, you should answer the questioner as much as possible based on what you know and recommend cheese products that the user may prefer.
        When the question is not in the form of a question, ask if there is anything else you would like to know based on the previous question.

        Context:
        {context}

        Question: {question}

        Answer: Let me help you with that. """

        prompt = ChatPromptTemplate.from_template(template)

        self.chain = (
            {"context": self.vectorstore.as_retriever(), "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def get_relevant_documents(self, query: str, k: int = 3) -> List[Dict]:
        """Retrieve relevant documents from the vector store."""
        docs = self.vectorstore.similarity_search(query, k)
        context = []
        for doc in docs:
            metadata = doc.metadata or {}
            context.append({
                "title": metadata.get("name", ""),
                "price": metadata.get("prices", {}).get("Each", ""),
                "brand": metadata.get("brand", ""),
                "product_url": metadata.get("href", ""),
                "image_url": metadata.get("showImage", ""),
            "description": metadata.get("description", "A delicious cheese product perfect for foodservice needs.")
            })
        return context

    def generate_response(self, query: str) -> Dict:
        """Generate a response using the RAG chain."""
        context = self.get_relevant_documents(query)
        response = self.chain.invoke(query)
        return {
            "response": response,
            "context": context
        }
