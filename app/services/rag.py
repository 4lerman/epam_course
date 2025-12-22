from app.utils.helpers import format_image_data_uri
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from base64 import b64decode
from rank_bm25 import BM25Okapi
from app.utils.helpers import format_image_data_uri
from app.core.config import config


def parse_docs(docs):
    """
    Separates retrieved documents into images (base64) and text.
    """
    b64 = []
    text = []
    for doc in docs:
        if not doc:
            continue
        content = getattr(doc, "page_content", doc)
        try:
            b64decode(content)
            b64.append(content)
        except Exception:
            text.append(content)
    return {"images": b64, "texts": text}


def build_prompt(payload):
    docs_by_type = payload["context"]
    user_question = payload["question"]

    context_text = ""
    if len(docs_by_type["texts"]) > 0:
        for text_element in docs_by_type["texts"]:
            context_text += str(text_element)

    prompt_template = f"""
    Answer the question based only on the following context, which can include text, tables, and below image.
    Context: {context_text}
    Question: {user_question}
    """

    prompt_content = [{"type": "text", "text": prompt_template}]

    if len(docs_by_type["images"]) > 0:
        for image in docs_by_type["images"]:
            prompt_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": format_image_data_uri(image)},
                }
            )

    return ChatPromptTemplate.from_messages([
        HumanMessage(content=prompt_content)
    ])


def get_rag_chain(retriever):
    """
    Builds the final RAG chain.
    """

    def rerank_context(payload):
        question = payload["question"]
        docs = payload["docs"]
        texts = docs.get("texts", [])
        images = docs.get("images", [])

        if not texts:
            return {"context": docs, "question": question}

        try:
            tokenized = [t.lower().split() for t in texts]
            bm25 = BM25Okapi(tokenized)
            scores = bm25.get_scores(question.lower().split())
            ranked = [t for _, t in sorted(zip(scores, texts), reverse=True)]
        except Exception:
            ranked = texts

        top_k = min(len(ranked), 6)
        return {"context": {"texts": ranked[:top_k], "images": images}, "question": question}

    chain = (
        {
            "docs": retriever | RunnableLambda(parse_docs),
            "question": RunnablePassthrough(),
        }
        | RunnableLambda(rerank_context)
        | RunnableLambda(build_prompt)
        | ChatOpenAI(model="gpt-4o-mini")
        | StrOutputParser()
    )
    return chain
