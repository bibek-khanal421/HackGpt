from langchain.memory import PostgresChatMessageHistory, ConversationBufferWindowMemory

class LangChainMemory:
    def __init__(self, connection_string:str, session_id:str):
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
            connection_string=self.connection_string, 
            session_id=self.session_id
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
    
    def get_memory(self):
        """
        Get the memory object for the current session.
        Args:
            None
        Returns:
            ConversationBufferWindowMemory: A ConversationBufferWindowMemory object
        """
        history = self.get_history()
        memory =  ConversationBufferWindowMemory(
            memory_key="history",
            return_messages=True,
            chat_memory=history,
            input_key="input",
            k=10,
            ai_prefix="AI",
            human_prefix="Human",
        )
        return memory
    
    
