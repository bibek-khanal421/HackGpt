from langchain.memory import PostgresChatMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from config import DB_TYPE


class LangChainMemory:
    def __init__(self, connection_string: str, session_id: str):
        self.connection_string = connection_string
        self.session_id = session_id
        self.db_type = DB_TYPE

    def postges_history(self):
        """
        Get the chat history for the current session.
        Args:
            None
        Returns:
            PostgresChatMessageHistory: A PostgresChatMessageHistory object.
        """
        history = PostgresChatMessageHistory(
            connection_string=self.connection_string, session_id=self.session_id
        )
        return history
    
    def sqlite_history(self):
        """
        Get the chat history for the current session.
        Args:
            None
        Returns:
            SQLChatMessageHistory: A SQLChatMessageHistory object.
        """
        history = SQLChatMessageHistory(
            connection_string=self.connection_string, session_id=self.session_id
        )
        return history

    def get_history(self):
        """
        Get the chat history for the current session.
        Args:
            None
        Returns:
            ChatMessageHistory: A ChatMessageHistory object.
        """
        if self.db_type == "postgres":
            history = self.postges_history()
        elif self.db_type == "sqlite":
            history = self.sqlite_history()
        return history

    def clear_history(self):
        """
        Clear the chat history for the current session.
        Args:
            None
        Returns:
            None
        """
        if self.db_type == "postgres":
            history = self.postges_history()
        elif self.db_type == "sqlite":
            history = self.sqlite_history()
        history.clear()
