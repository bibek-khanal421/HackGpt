from langchain_community.tools import DuckDuckGoSearchResults
from tools.scraper import scrape_websites
from langchain_core.runnables.history import RunnableWithMessageHistory
from source.chain import get_chain
from langchain.prompts import PromptTemplate
from config import LLM_TYPE
from source.chain import LLMFactory
from datetime import datetime

class LangChainToolManager:
    def __init__(self):
        self.tools = {
            "duckduckgo": self.duckduckgo_search
        }
    
    def condense_question(self, query, temperature, model, history, session_id, hackprompt):
        prompt = f"""
            Current System Date: {datetime.now().strftime("%Y-%m-%d")}
            Current Weekday: {datetime.now().strftime("%A")}""" + """
            Previous Conversation History: {history}
            These are some extra information provided by the user to help you better understand the task:
            {hackprompt}
            The user asked the following question:
            {query}
            Your task is to formulate a concise question based on the user input, extra information, and the past conversation history.
            The question you generate will be used to search the web for relevant information and return a single question and nothing else. 
            NOTE: the system date and weekday can be used where required.
            Try to include all the details into the question to make it more concise and specific
            Question:
            """
        # creating runnable
        runnable_chain = RunnableWithMessageHistory(
            get_chain(temperature=0.7, model=model, prompt=prompt, input_variables=["query", "history"]),
            lambda session_id: history,
            input_messages_key="input",
            history_messages_key="history",
        )
        config = {"configurable": {"session_id": session_id}}
        response = runnable_chain.invoke({"query": query, "history": history, "hackprompt": hackprompt}, config).content
        print("Condensed question:", response)
        return response

    def duckduckgo_search(self, query, temperature, model, history, session_id, hackprompt):
        condensed_query = self.condense_question(query, temperature, model, history, session_id, hackprompt)
        print("Condensed query:", condensed_query)
        response = DuckDuckGoSearchResults(output_format="list", max_results=7).run(condensed_query)
        links = [result["link"] for result in response]
        return scrape_websites(links, query)


    
    