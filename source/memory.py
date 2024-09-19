from langchain.memory import PostgresChatMessageHistory


class LangChainMemory:
    def __init__(self, connection_string: str, session_id: str):
        self.connection_string = connection_string
        self.session_id = session_id

    def get_history(self):
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

    def clear_history(self):
        """
        Clear the chat history for the current session.
        Args:
            None
        Returns:
            None
        """
        history = self.get_history()
        history.clear()
