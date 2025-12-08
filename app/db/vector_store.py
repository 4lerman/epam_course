import uuid
from langchain_chroma import Chroma
from langchain_core.stores import InMemoryStore
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_classic.retrievers.multi_vector import MultiVectorRetriever
from app.core.config import config


class VectorStoreManager:
    def __init__(self):
        # The vectorstore to use to index the child chunks
        self.vectorstore = Chroma(
            collection_name="multi_modal_rag",
            embedding_function=OpenAIEmbeddings()
        )

        self.store = InMemoryStore()
        self.id_key = "doc_id"

        self.retriever = MultiVectorRetriever(
            vectorstore=self.vectorstore,
            docstore=self.store,
            id_key=self.id_key,
        )

    def add_documents(self, summaries, original_contents):
        doc_ids = [str(uuid.uuid4()) for _ in original_contents]

        summary_docs = [
            Document(page_content=s, metadata={self.id_key: doc_ids[i]})
            for i, s in enumerate(summaries)
        ]

        self.vectorstore.add_documents(summary_docs)

        self.store.mset(list(zip(doc_ids, original_contents)))
