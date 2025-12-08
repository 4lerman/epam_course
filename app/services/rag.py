from app.utils.helpers import format_image_data_uri
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from base64 import b64decode
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
        try:
            b64decode(doc)
            b64.append(doc)
        except Exception:
            text.append(doc)
    return {"images": b64, "texts": text}


def build_prompt(kwargs):
    docs_by_type = kwargs["context"]
    user_question = kwargs["question"]

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
    chain = (
        {
            "context": retriever | RunnableLambda(parse_docs),
            "question": RunnablePassthrough(),
        }
        | RunnableLambda(build_prompt)
        | ChatOpenAI(model="gpt-4o-mini")
        | StrOutputParser()
    )
    return chain
