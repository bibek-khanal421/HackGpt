import os
import re
import uuid
import pickle
import time

import streamlit as st
from langchain_core.runnables.history import RunnableWithMessageHistory

from config import DATABASE_URL, OPENAI_API_KEY, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
from prompt.prompt import get_prompt
from source.chain import get_chain
from source.chat_session import ChatSession, SessionLocal
from source.memory import LangChainMemory
from source.pdf_processor import PDFProcessor, PDFDocument

st.set_page_config(layout="wide")

if "current_session_name" not in st.session_state:
    st.session_state.current_session_name = None
if "pdf_processing" not in st.session_state:
    st.session_state.pdf_processing = False
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "current_file" not in st.session_state:
    st.session_state.current_file = None
if "session_files" not in st.session_state:
    st.session_state.session_files = []

CHAT_PROMPT_TEMPLATE_FILE = r"./prompt/chatprompt.tmpl"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["AZURE_OPENAI_API_KEY"] = AZURE_OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = AZURE_OPENAI_ENDPOINT


class ChatApp:
    def __init__(self):
        self.db = SessionLocal()
        self.pdf_processor = PDFProcessor()

    def create_session(
        self, session_name="Session", model="gpt-4o", temperature=0.5, hack_prompt=""
    ):
        session_name = f"{session_name}_{uuid.uuid4().hex[:8]}"
        new_session = ChatSession(
            session_name=session_name,
            model=model,
            temperature=temperature,
            hack_prompt=hack_prompt,
        )
        self.db.add(new_session)
        self.db.commit()

        st.session_state.current_session_name = session_name
        st.session_state.model = model
        st.session_state.temperature = temperature
        st.session_state.hack_prompt = hack_prompt
        st.session_state.current_file = None
        st.session_state.session_files = []
        st.success(f"Session '{session_name}' created and active.")

    def get_session_files(self, session_name: str) -> list:
        """Get list of PDF files for a session."""
        pdf_docs = (
            self.db.query(PDFDocument)
            .filter(PDFDocument.session_id == session_name)
            .all()
        )
        return [doc.filename for doc in pdf_docs]

    def switch_session(self, session_name):
        with st.spinner("Loading session..."):
            session = (
                self.db.query(ChatSession)
                .filter(ChatSession.session_name == session_name)
                .first()
            )
            if session:
                st.session_state.current_session_name = session_name
                st.session_state.model = session.model
                st.session_state.temperature = session.temperature
                st.session_state.hack_prompt = session.hack_prompt
                # Get session files
                st.session_state.session_files = self.get_session_files(session_name)
                if st.session_state.session_files:
                    st.session_state.pdf_processed = True
                    st.session_state.current_file = st.session_state.session_files[-1]
                else:
                    st.session_state.pdf_processed = False
                    st.session_state.current_file = None

    def delete_session(self, session_name):
        session = (
            self.db.query(ChatSession)
            .filter(ChatSession.session_name == session_name)
            .first()
        )
        if session:
            self.db.delete(session)
            self.db.commit()
            st.success(f"Session '{session_name}' deleted.")
            st.session_state.current_session_name = None
            st.session_state.model = None
            st.session_state.temperature = None
            st.session_state.hack_prompt = None
            st.session_state.pdf_processed = False
            st.session_state.current_file = None
            st.session_state.session_files = []
        else:
            st.error(f"Session '{session_name}' does not exist.")

    def process_pdf(self, pdf_file, session_name):
        """Process uploaded PDF file and store embeddings."""
        try:
            st.session_state.pdf_processing = True
            
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Update status
            status_text.text(f"Processing {pdf_file.name}...")
            progress_bar.progress(10)
            
            # Process PDF and create embeddings
            index, chunks = self.pdf_processor.process_pdf(pdf_file)
            progress_bar.progress(50)
            status_text.text("Creating embeddings...")
            
            # Store in database
            pdf_doc = PDFDocument(
                session_id=session_name,
                filename=pdf_file.name,
                embeddings=pickle.dumps(index),
                chunks=pickle.dumps(chunks)
            )
            self.db.add(pdf_doc)
            self.db.commit()
            progress_bar.progress(90)
            status_text.text("Finalizing...")
            
            st.session_state.pdf_processed = True
            st.session_state.current_file = pdf_file.name
            st.session_state.session_files.append(pdf_file.name)
            
            # Complete the progress
            progress_bar.progress(100)
            status_text.text("Done!")
            time.sleep(0.5)  # Show 100% for a moment
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"Successfully processed {pdf_file.name}")
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            st.session_state.pdf_processed = False
            st.session_state.current_file = None
        finally:
            st.session_state.pdf_processing = False
            st.rerun()

    def get_pdf_context(self, query: str, session_name: str) -> str:
        """Get relevant context from PDF documents for the query."""
        pdf_docs = (
            self.db.query(PDFDocument)
            .filter(PDFDocument.session_id == session_name)
            .all()
        )
        
        if not pdf_docs:
            return ""
        
        context = []
        for doc in pdf_docs:
            index = pickle.loads(doc.embeddings)
            chunks = pickle.loads(doc.chunks)
            relevant_chunks = self.pdf_processor.search_similar_chunks(query, index, chunks)
            context.extend(relevant_chunks)
        
        return "\n".join(context)

    def chat(
        self, input_text, history, model, temperature, hack_prompt, session_id
    ):
        """
        Function to chat with the OpenAI model.
        Args:
            input_text (str): The input text from the user.
            memory (ConversationBufferWindowMemory): The memory object for the current session.
            model (str): The name of the model to use.
            temperature (float): The temperature parameter for sampling.
            hack_prompt (str): The additional prompt to use.
        Returns:
            str: The response from the OpenAI model.
        """
        if st.session_state.current_session_name is None:
            st.error("No active session. Please create a session first.")
            return ""

        # Get relevant context from PDF documents
        pdf_context = self.get_pdf_context(input_text, session_id)
        print(pdf_context)
        prompt = get_prompt(
            path=CHAT_PROMPT_TEMPLATE_FILE,
            vars={
                "hackprompt": hack_prompt if hack_prompt else "No additional prompt",
                "input": "{input}",
                "history": "{history}",
                "pdf_context": pdf_context if pdf_context else "No relevant context from PDF documents",
            },
        )
        # creating runnable
        runnable_chain = RunnableWithMessageHistory(
            get_chain(temperature=temperature, model=model, prompt=prompt),
            lambda session_id: history,
            input_messages_key="input",
            history_messages_key="history",
        )
        config = {"configurable": {"session_id": session_id}}
        response = runnable_chain.stream({"input": input_text}, config)
        return response

    def delete_pdf_document(self, session_name: str, filename: str):
        """Delete a PDF document from the session."""
        pdf_doc = (
            self.db.query(PDFDocument)
            .filter(
                PDFDocument.session_id == session_name,
                PDFDocument.filename == filename
            )
            .first()
        )
        if pdf_doc:
            self.db.delete(pdf_doc)
            self.db.commit()
            # Update session state
            st.session_state.session_files.remove(filename)
            if not st.session_state.session_files:
                st.session_state.pdf_processed = False
                st.session_state.current_file = None
            else:
                st.session_state.current_file = st.session_state.session_files[-1]
            return True
        return False


def format_response(response):
    """
    Function to break down OpenAI markdown response and format it properly in Streamlit.
    Args:
        response (str): The response from OpenAI.
    Returns:
        None
    """
    lines = response.split("\n")
    code_block = False
    code_lines = []

    for line in lines:
        # Handle code block
        if line.startswith("```"):
            if code_block:  # If we're closing a code block
                st.code("\n".join(code_lines), language="python")
                code_block = False
                code_lines = []
            else:  # If we're opening a code block
                code_block = True
        elif code_block:
            code_lines.append(line)

        # Handle headers (Markdown headers)
        elif re.match(r"^# .+", line):
            st.markdown(f"## {line[2:]}")
        elif re.match(r"^## .+", line):
            st.markdown(f"### {line[3:]}")
        elif re.match(r"^### .+", line):
            st.markdown(f"#### {line[4:]}")

        # Handle bullet points (unordered list)
        elif line.startswith("- "):
            st.markdown(f"* {line[2:]}")

        # Handle normal text
        elif line.strip():  # Skip empty lines
            st.markdown(line)


def main():
    st.title("HackGpt")

    st.markdown(
        """
    <style>
        section[data-testid="stSidebar"] {
            width: 400px !important; # Set the width to your desired value
        }
        <style>
    </style>
    """,
        unsafe_allow_html=True,
    )
    app = ChatApp()
    memory = LangChainMemory(
        connection_string=DATABASE_URL, session_id=st.session_state.current_session_name
    )
    chat_memory = memory.get_history().messages
    # Sidebar for session management
    text = st.sidebar.text_input("Enter Session Name (OPTIONAL)")
    if st.sidebar.button("Create New Session"):
        app.create_session(text if text else "Session")
        st.rerun()

    session_names = [
        session.session_name for session in app.db.query(ChatSession).all()
    ][::-1]

    if len(session_names) > 0:
        st.sidebar.title("Available Sessions")
    else:
        st.sidebar.write("No Sessions Available")

    for name in session_names:
        button = st.sidebar.button(name.split("_")[0] if not "Session" in name else name, key=name, use_container_width=True, type="primary")
        if button:
            app.switch_session(name)
            st.rerun()

    if st.session_state.current_session_name:
        with st.sidebar.expander("Configuration", expanded=True):
            if st.button("Clear Session Memory", key="clear"):
                if st.session_state.current_session_name is None:
                    st.error("No active session. Please create a session first.")
                else:
                    memory.clear_history()
                    st.rerun()

            model = st.selectbox(
                "Choose Your Model",
                ("gpt-4o", "gpt-4o-mini", "gpt-4"),
                index=["gpt-4o", "gpt-4o-mini", "gpt-4"].index(st.session_state.model),
            )
            temperature = st.slider(
                "Select Your Temperature", 0.0, 1.0, st.session_state.temperature
            )
            hack_prompt = st.text_area(
                "Hack Prompt", value=st.session_state.hack_prompt, height=400
            )

            # PDF Upload Section
            st.sidebar.markdown("---")
            st.sidebar.subheader("PDF Upload (Optional)")
            
            # Show uploaded files with delete buttons
            if st.session_state.session_files:
                st.sidebar.write("Uploaded PDFs:")
                for file in st.session_state.session_files:
                    col1, col2 = st.sidebar.columns([3, 1])
                    with col1:
                        st.write(f"- {file}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{file}"):
                            if app.delete_pdf_document(st.session_state.current_session_name, file):
                                st.success(f"Deleted {file}")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete {file}")
            
            uploaded_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
            if uploaded_file is not None and not st.session_state.pdf_processing:
                if uploaded_file.name != st.session_state.current_file:
                    app.process_pdf(uploaded_file, st.session_state.current_session_name)

            if st.button("Delete Session", key="delete"):
                app.delete_session(st.session_state.current_session_name)
                st.rerun()

            # Update session settings
            session = (
                app.db.query(ChatSession)
                .filter(
                    ChatSession.session_name == st.session_state.current_session_name
                )
                .first()
            )
            if session:
                session.model = model
                session.temperature = temperature
                session.hack_prompt = hack_prompt
                app.db.commit()

        st.write(f"**Current Session**: {st.session_state.current_session_name}")
        
        # Show chat history
        for convo in chat_memory:
            if convo.type == "human":
                with st.chat_message("user"):
                    st.text(convo.content)
            elif convo.type == "AIMessageChunk":
                with st.chat_message("ai"):
                    st.write(convo.content)

        # Input for user to type a message
        if st.session_state.pdf_processing:
            st.info("Please wait while the PDF is being processed...")
            user_input = st.chat_input("Processing PDF...", disabled=True)
        else:
            user_input = st.chat_input("Type your message here...")

        if user_input:
            with st.chat_message("user"):
                st.text(str(user_input))
            stream = app.chat(
                user_input,
                memory.get_history(),
                model,
                temperature,
                hack_prompt,
                st.session_state.current_session_name,
            )
            with st.chat_message("ai"):
                st.write_stream(stream)
    else:
        st.write("No session active. Please create a session.")


if __name__ == "__main__":
    main()
