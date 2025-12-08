import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import tempfile
from app.main import ChatWithPDFApp

st.set_page_config(layout="wide", page_title="ChatWithPDF")

def main():
    st.title("Chat with your PDF")
    
    # Session state initialization
    if "app" not in st.session_state:
        st.session_state.app = ChatWithPDFApp()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "ingested" not in st.session_state:
        st.session_state.ingested = False

    # Sidebar for upload
    with st.sidebar:
        st.header("Upload Document")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None and not st.session_state.ingested:
            if st.button("Process PDF"):
                with st.spinner("Processing... This may take a while as we extract images and text."):
                    # Save uploaded file to temp
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        try:
                            st.session_state.app.ingest(temp_path)
                            st.session_state.ingested = True
                            st.success("PDF Processed Successfully!")
                        except Exception as e:
                            st.error(f"Error processing PDF: {e}")

    # Chat Interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about the PDF"):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            if not st.session_state.ingested:
                response = "Please upload and process a PDF first."
                st.write(response)
            else:
                with st.spinner("Thinking..."):
                    response = st.session_state.app.query(prompt)
                    st.write(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
