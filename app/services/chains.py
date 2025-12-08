from app.utils.helpers import format_image_data_uri
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from app.core.config import config


def get_summarize_chain():
    """
    Returns a chain for summarizing text and tables using Groq (Llama 3.1).
    """
    prompt_text = '''
    You are an assistant tasked with summarizing tables and text.
    Give a concise summary of the table or text.

    Respond only with the summary, no additional comment.
    Do not start your message by saying "Here is a summary" or anything like that.

    Table or text chunk: {element}
    '''
    prompt = ChatPromptTemplate.from_template(prompt_text)
    model = ChatGroq(temperature=0.5, model="llama-3.1-8b-instant",
                     api_key=config.GROQ_API_KEY)
    return prompt | model | StrOutputParser()


def get_image_describe_chain():
    """
    Creates a chain for describing images using OpenAI Vision model.
    """
    model = ChatOpenAI(model="gpt-4o-mini", api_key=config.OPENAI_API_KEY)

    def create_vision_prompt(image_data):
        prompt_text = """Describe the image in detail. For context,
                          the image is part of a research paper explaining the transformers
                          architecture. Be specific about graphs, such as bar plots."""
        return [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": format_image_data_uri(image_data)},
                    },
                ]
            )
        ]

    chain = (
        RunnableLambda(create_vision_prompt)
        | model
        | StrOutputParser()
    )

    return chain
