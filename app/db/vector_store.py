import uuid
from langchain_chroma import Chroma
from langchain_core.stores import InMemoryStore
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_classic.retrievers.multi_vector import MultiVectorRetriever
from langchain_community.retrievers import BM25Retriever
from typing import Optional, Sequence
from app.core.config import config


class HybridRetriever:
    """
    Combines multi-vector semantic retrieval with lexical BM25 and
    returns de-duplicated Documents for downstream chains.
    """

    def __init__(self, multi_retriever, bm25_retriever, store, id_key="doc_id"):
        self.multi_retriever = multi_retriever
        self.bm25_retriever = bm25_retriever
        self.store = store
        self.id_key = id_key

    def _as_document(self, item):
        if isinstance(item, Document):
            return item
        return Document(page_content=str(item), metadata={})

    def _hydrate_doc(self, doc: Document):
        if doc.page_content:
            return doc
        doc_id = doc.metadata.get(self.id_key)
        if doc_id:
            raw = self.store.mget([doc_id])[0]
            if raw:
                return Document(page_content=raw, metadata=doc.metadata)
        return doc

    def get_relevant_documents(self, query):
        docs = []
        if self.multi_retriever:
            try:
                docs.extend(self.multi_retriever.get_relevant_documents(query))
            except AttributeError:
                docs.extend(self.multi_retriever.invoke(query))
        if self.bm25_retriever:
            try:
                docs.extend(self.bm25_retriever.get_relevant_documents(query))
            except AttributeError:
                docs.extend(self.bm25_retriever.invoke(query))

        unique = []
        seen = set()
        for doc in docs:
            doc = self._as_document(doc)
            doc = self._hydrate_doc(doc)
            doc_id = doc.metadata.get(self.id_key)
            key = doc_id or doc.page_content
            if key in seen:
                continue
            seen.add(key)
            unique.append(doc)
        return unique

    def invoke(self, query):
        return self.get_relevant_documents(query)

    async def ainvoke(self, query):
        return self.get_relevant_documents(query)


class VectorStoreManager:
    def __init__(
        self,
        embedding_function=None,
        enable_hybrid: bool = True,
        bm25_k: int = 4,
    ):
        # The vectorstore to use to index the child chunks
        self.embedding_function = embedding_function or OpenAIEmbeddings()
        self.vectorstore = Chroma(
            collection_name="multi_modal_rag",
            embedding_function=self.embedding_function,
        )

        self.store = InMemoryStore()
        self.id_key = "doc_id"
        self.enable_hybrid = enable_hybrid
        self.bm25_retriever = None
        self.bm25_corpus: list[Document] = []
        self.bm25_k = bm25_k

        self.multi_retriever = MultiVectorRetriever(
            vectorstore=self.vectorstore,
            docstore=self.store,
            id_key=self.id_key,
        )

        self.retriever = self.multi_retriever

    def _ensure_bm25(self):
        if not self.bm25_corpus:
            return
        self.bm25_retriever = BM25Retriever.from_documents(
            self.bm25_corpus, k=self.bm25_k
        )

        if self.enable_hybrid:
            self.retriever = HybridRetriever(
                self.multi_retriever, self.bm25_retriever, self.store, self.id_key
            )

    def add_documents(
        self,
        summaries: Sequence[str],
        original_contents: Sequence[str],
        bm25_texts: Optional[Sequence[str]] = None,
    ):
        doc_ids = [str(uuid.uuid4()) for _ in original_contents]

        summary_docs = [
            Document(page_content=s, metadata={self.id_key: doc_ids[i]})
            for i, s in enumerate(summaries)
        ]

        self.vectorstore.add_documents(summary_docs)
        self.store.mset(list(zip(doc_ids, original_contents)))

        bm25_inputs = bm25_texts or summaries
        new_bm25_docs = [
            Document(page_content=bm25_inputs[i], metadata={self.id_key: doc_ids[i]})
            for i in range(len(bm25_inputs))
        ]
        self.bm25_corpus.extend(new_bm25_docs)
        self._ensure_bm25()
