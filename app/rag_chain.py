from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.vectorstores import Pinecone
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
        template = """You are a helpful cheese expert assistant. Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just recommend asking only cheese-related questions, don't try to make up an answer.

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
        docs = self.vectorstore.similarity_search(query, k=k)
        context = []
        for doc in docs:
            metadata = doc.metadata or {}
            context.append({
                "title": metadata.get("title", ""),
                "price": metadata.get("price", ""),
                "brand": metadata.get("brand", ""),
                "product_url": metadata.get("product_url", ""),
                "image_url": metadata.get("image_url", "")
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
