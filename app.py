import os
import re
import uuid

import streamlit as st
from langchain_core.runnables.history import RunnableWithMessageHistory

from config import DATABASE_URL, OPENAI_API_KEY, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
from prompt.prompt import get_prompt
from source.chain import get_chain
from source.chat_session import ChatSession, SessionLocal
from source.memory import LangChainMemory

st.set_page_config(layout="wide")

if "current_session_name" not in st.session_state:
    st.session_state.current_session_name = None

CHAT_PROMPT_TEMPLATE_FILE = r"/home/lis-bibek-khanal/hackgpt/prompt/chatprompt.tmpl"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["AZURE_OPENAI_API_KEY"] = AZURE_OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = AZURE_OPENAI_ENDPOINT


class ChatApp:
    def __init__(self):
        self.db = SessionLocal()

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
        st.success(f"Session '{session_name}' created and active.")

    def switch_session(self, session_name):
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
        else:
            st.error(f"Session '{session_name}' does not exist.")

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

        prompt = get_prompt(
            path=CHAT_PROMPT_TEMPLATE_FILE,
            vars={
                "hackprompt": hack_prompt if hack_prompt else "No additional prompt",
                "input": "{input}",
                "history": "{history}",
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
        for convo in chat_memory:
            if convo.type == "human":
                with st.chat_message("user"):
                    st.text(convo.content)
            elif convo.type == "AIMessageChunk":
                with st.chat_message("ai"):
                    st.write(convo.content)

        # Input for user to type a message
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
