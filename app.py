import streamlit as st
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
import uuid
from langchain_core.prompts.prompt import PromptTemplate
import re
from source.memory import LangChainMemory
from source.chat_session import ChatSession, SessionLocal
from config import DATABASE_URL, OPENAI_API_KEY
from prompt.prompt import get_prompt
import os

st.set_page_config(layout="wide")

if "current_session_name" not in st.session_state:
    st.session_state.current_session_name = None

CHAT_PROMPT_TEMPLATE_FILE="/home/lis-bibek-khanal/hackgpt/prompt/chatprompt.tmpl"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# class ChatApp:
#     def __init__(self):
#         self.db = SessionLocal()

#     def create_session(self, session_name="Session"):
#         """
#         Function to create a new chat session.
#         Args:
#             None
#         Returns:
#             None
#         """
#         session_name = f"{session_name}_{uuid.uuid4().hex[:8]}"
#         new_session = ChatSession(session_name=session_name)
#         self.db.add(new_session)
#         self.db.commit()

#         st.session_state.current_session_name = session_name
#         st.success(f"Session '{session_name}' created and active.")

#     def switch_session(self, session_name):
#         """
#         Function to switch the active chat session.
#         Args:
#             session_name (str): The name of the session to switch to.
#         Returns:
#             None
#         """
#         st.session_state.current_session_name = session_name

#     def delete_session(self, session_name):
#         """
#         Function to delete a chat session.
#         Args:
#             session_name (str): The name of the session to delete.
#         Returns:
#             None
#         """
#         session = self.db.query(ChatSession).filter(ChatSession.session_name == session_name).first()
#         if session:
#             self.db.delete(session)
#             self.db.commit()
#             st.success(f"Session '{session_name}' deleted.")
#             st.session_state.current_session_name = None
#         else:
#             st.error(f"Session '{session_name}' does not exist.")
class ChatApp:
    def __init__(self):
        self.db = SessionLocal()

    def create_session(self, session_name="Session", model="gpt-4o", temperature=0.5, hack_prompt=""):
        session_name = f"{session_name}_{uuid.uuid4().hex[:8]}"
        new_session = ChatSession(session_name=session_name, model=model, temperature=temperature, hack_prompt=hack_prompt)
        self.db.add(new_session)
        self.db.commit()

        st.session_state.current_session_name = session_name
        st.session_state.model = model
        st.session_state.temperature = temperature
        st.session_state.hack_prompt = hack_prompt
        st.success(f"Session '{session_name}' created and active.")

    def switch_session(self, session_name):
        session = self.db.query(ChatSession).filter(ChatSession.session_name == session_name).first()
        if session:
            st.session_state.current_session_name = session_name
            st.session_state.model = session.model
            st.session_state.temperature = session.temperature
            st.session_state.hack_prompt = session.hack_prompt

    def delete_session(self, session_name):
        session = self.db.query(ChatSession).filter(ChatSession.session_name == session_name).first()
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

    def chat(self, input_text, memory, model, temperature, hack_prompt):
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
        
        prompt = get_prompt(path=CHAT_PROMPT_TEMPLATE_FILE, vars={"hackprompt": hack_prompt if hack_prompt else "No additional prompt", "input":"{input}", "history":"{history}"})
        # Create conversation chain with the message history
        chain = ConversationChain(
            llm=ChatOpenAI(temperature=temperature, model=model), 
            memory=memory,
            prompt = PromptTemplate(
                input_variables=["input","history"],
                template=prompt
            )
        )
        # Get the response from the model
        response = chain.predict(input=input_text)
        return response

def write_markdown(markdown):
    """
    Function to write markdown text to the Streamlit app.
    Args:
        markdown (str): The markdown text to write.
    Returns:
        None
    """
    # Split the markdown into lines
    lines = markdown.split('\n')

    # Loop through each line
    for line in lines:
        # Check if the line starts with a code block
        if line.startswith('```'):
            # Get the code inside the code block
            code = line[3:-3]

            # Write the code using st.code
            st.code(code)
        else:
            # Write the line using st.write
            st.write(line)

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

def summarize_conversation(memory):
        """
        Function to summarize the conversation.
        Args:
            memory (ConversationBufferWindowMemory): The memory object for the current session.
        Returns:
            str: The summary of the conversation.
        """
        history = memory.load_memory_variables({}).get("history", [])
        conversation_text = " ".join([convo.content for convo in history if convo.type in ["human", "ai"]])
        # Summarize the conversation with token size 5
        summary = ChatOpenAI(temperature=0.5, model="gpt-4o").predict(text=f"Summarize this conversation so that i could use it as a session name in 3 words: {str(conversation_text)}")
        return ''.join(letter for letter in summary if letter.isalnum())

# def main():
#     st.title("HackGpt")

#     st.markdown(
#     """
#     <style>
#         section[data-testid="stSidebar"] {
#             width: 300px !important; # Set the width to your desired value
#         }
#     </style>
#     """,
#     unsafe_allow_html=True,
#     )

#     app = ChatApp()
#     memory = LangChainMemory(connection_string=DATABASE_URL, session_id=st.session_state.current_session_name).get_memory()
#     # Sidebar for session management
#     text = st.sidebar.text_input("Enter Session Name (OPTIONAL)")
#     if st.sidebar.button("Create New Session"):
#         app.create_session(text if text else "Session")
#         st.rerun()
    
#     session_names = [session.session_name for session in app.db.query(ChatSession).all()][::-1]
#     if len(session_names) > 0:
#         st.sidebar.title("Available Sessions")
#     else:
#         st.sidebar.write("No Sessions Available")

#     for name in session_names:
#         button = st.sidebar.button(name, key=name)
#         if button:
#             app.switch_session(name)
#             st.rerun()
    
#     if st.session_state.current_session_name:
#         with st.sidebar.expander("Configuration", expanded=True):
#             if st.button("Clear Session Memory", key="clear"):
#                 if st.session_state.current_session_name is None:
#                     st.error("No active session. Please create a session first.")
#                 else:
#                     memory.clear_history()
#             model = st.selectbox(
#                 "Choose Your Model",
#                 ("gpt-4o", "gpt-4o-mini", "gpt-4"),
#             )
#             temperature = st.slider("Select Your Temperature", 0.0,1.0,0.5)
#             hack_prompt = st.text_area("Hack Prompt")
#             if st.button("Delete Session", key="delete"):
#                 app.delete_session(st.session_state.current_session_name)
#                 st.rerun()
            

#         st.write(f"**Current Session**: {st.session_state.current_session_name}")
#         history = memory.load_memory_variables({}).get("history", [])
#         for convo in history:
#             if convo.type=="human":
#                 with st.chat_message("user"):
#                     st.text(convo.content)
#             elif convo.type=="ai":
#                 with st.chat_message("ai"):
#                     st.write(convo.content)

#         # Input for user to type a message
#         user_input = st.chat_input("Type your message here...") 
        
#         if user_input:
#             with st.chat_message("user"):
#                 st.text(str(user_input))
#             with st.spinner("processing..."):
#                 response = app.chat(user_input, memory, model, temperature, hack_prompt)
#                 with st.chat_message("ai"):
#                     st.write(response)
#                     # write_markdown(response)
#     else:
#         st.write("No session active. Please create a session.")

def main():
    st.title("HackGpt")

    st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 300px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
    )

    app = ChatApp()
    memory = LangChainMemory(connection_string=DATABASE_URL, session_id=st.session_state.current_session_name).get_memory()
    # Sidebar for session management
    text = st.sidebar.text_input("Enter Session Name (OPTIONAL)")
    if st.sidebar.button("Create New Session"):
        app.create_session(text if text else "Session")
        st.rerun()

    session_names = [session.session_name for session in app.db.query(ChatSession).all()][::-1]
    if len(session_names) > 0:
        st.sidebar.title("Available Sessions")
    else:
        st.sidebar.write("No Sessions Available")

    for name in session_names:
        button = st.sidebar.button(name, key=name)
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

            model = st.selectbox(
                "Choose Your Model",
                ("gpt-4o", "gpt-4o-mini", "gpt-4"),
                index=["gpt-4o", "gpt-4o-mini", "gpt-4"].index(st.session_state.model)
            )
            temperature = st.slider("Select Your Temperature",0.0,1.0,st.session_state.temperature)
            hack_prompt = st.text_area("Hack Prompt", value=st.session_state.hack_prompt)

            if st.button("Delete Session", key="delete"):
                app.delete_session(st.session_state.current_session_name)
                st.rerun()

            # Update session settings
            session = app.db.query(ChatSession).filter(ChatSession.session_name == st.session_state.current_session_name).first()
            if session:
                session.model = model
                session.temperature = temperature
                session.hack_prompt = hack_prompt
                app.db.commit()

        st.write(f"**Current Session**: {st.session_state.current_session_name}")
        history = memory.load_memory_variables({}).get("history", [])
        for convo in history:
            if convo.type=="human":
                with st.chat_message("user"):
                    st.text(convo.content)
            elif convo.type=="ai":
                with st.chat_message("ai"):
                    st.write(convo.content)

        # Input for user to type a message
        user_input = st.chat_input("Type your message here...") 

        if user_input:
            with st.chat_message("user"):
                st.text(str(user_input))
            with st.spinner("processing..."):
                response = app.chat(user_input, memory, model, temperature, hack_prompt)
                with st.chat_message("ai"):
                    st.write(response)
                    # write_markdown(response)
    else:
        st.write("No session active. Please create a session.")

if __name__ == "__main__":
    main()

