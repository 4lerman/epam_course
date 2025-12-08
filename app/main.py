import os
import time
from app.services.chains import get_summarize_chain, get_image_describe_chain
from app.services.rag import get_rag_chain
from app.db.vector_store import VectorStoreManager
from app.utils.pdf import process_pdf
from app.utils.helpers import get_images_base64
from app.core.config import config


class ChatWithPDFApp:
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.summarize_chain = get_summarize_chain()
        self.image_describe_chain = get_image_describe_chain()
        self.rag_chain = None

    def ingest(self, pdf_path):
        """
        Ingest a PDF file:
        1. Process PDF to extract elements (text, tables, images).
        2. Summarize extracted elements using Groq.
        3. Add summaries and original content to the vectorstore.
        4. Initialize the RAG chain.
        """
        # Ensure image output directory exists
        image_output_dir = os.path.dirname(pdf_path)

        # 1. Process PDF
        print("Starting PDF partitioning...")
        raw_pdf_elements, texts, tables = process_pdf(
            pdf_path, image_output_dir)
        print(
            f"Partitioning complete. Found {len(texts)} texts and {len(tables)} tables.")

        # 2. Extract Text Summaries
        if texts:
            print("Summarizing texts...")
            text_summaries = []
            for i, text in enumerate(texts):
                summary = self.summarize_chain.invoke(text)
                text_summaries.append(summary)
                print(f"Processed text chunk {i+1}/{len(texts)}")
                time.sleep(15)  # Increased delay to 15s for rate limits
            self.vector_store_manager.add_documents(text_summaries, texts)
            print("Text summarization complete.")

        # 3. Extract Table Summaries
        if tables:
            print("Summarizing tables...")
            tables_html = [table.metadata.text_as_html for table in tables]
            tables_summaries = []
            for i, table_html in enumerate(tables_html):
                summary = self.summarize_chain.invoke(table_html)
                tables_summaries.append(summary)
                print(f"Processed table {i+1}/{len(tables)}")
                time.sleep(15)
            self.vector_store_manager.add_documents(tables_summaries, tables)
            print("Table summarization complete.")

        # 4. Extract Image Summaries
        input_images_base64 = get_images_base64(raw_pdf_elements)

        if input_images_base64:
            print(f"Found {len(input_images_base64)} images. summarizing...")
            images_summaries = []
            for i, img_b64 in enumerate(input_images_base64):
                summary = self.image_describe_chain.invoke(img_b64)
                images_summaries.append(summary)
                print(f"Processed image {i+1}/{len(input_images_base64)}")
                # OpenAI has higher limits, so we don't need the long sleep here
            self.vector_store_manager.add_documents(
                images_summaries, input_images_base64)
            print("Image summarization complete.")

        # 5. Initialize RAG Chain
        print("Initializing RAG chain...")
        self.rag_chain = get_rag_chain(self.vector_store_manager.retriever)
        print("Ingestion complete.")

    def query(self, question):
        """
        Answers a user question.
        """
        if not self.rag_chain:
            return "Please ingest a document first."

        return self.rag_chain.invoke(question)
