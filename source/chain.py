from langchain_core.prompts.prompt import PromptTemplate
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from config import AZURE_DEPLOYMENT, API_VERSION, LLM_TYPE
from abc import ABC, abstractmethod

class LLM(ABC):
    @abstractmethod
    def get_llm(self, **kwargs):
        NotImplemented
    

class OpenAI(LLM):
    def get_llm(self,**kwargs):
        """
        Get the LLM for the current session.
        Args:
            llm (ChatOpenAI): The OpenAI model to use.
        Returns:
            LLMChain: A LLMChain object.
        """
        temperature = kwargs.get("temperature") if kwargs.get("temperature") else ValueError("Temperature is required")
        model = kwargs.get("model") if kwargs.get("model") else ValueError("Model is required")
        streaming = kwargs.get("streaming") if kwargs.get("streaming") else False
        return ChatOpenAI(temperature=temperature, model=model, streaming=streaming)

class AzureOpenAI(LLM):
    def get_llm(self,**kwargs):
        """
        Get the LLM for the current session.
        Args:
            llm (ChatOpenAI): The OpenAI model to use.
        Returns:
            LLMChain: A LLMChain object.
        """
        temperature = kwargs.get("temperature") if kwargs.get("temperature") else ValueError("Temperature is required")
        model = kwargs.get("model") if kwargs.get("model") else ValueError("Model is required")
        return AzureChatOpenAI(
            azure_deployment=AZURE_DEPLOYMENT,
            api_version=API_VERSION,
            temperature=temperature,
            model=model
        )

class LLMFactory():
    def __init__(self, type):
        self.type = type
        self.llms = {
            "azure": AzureOpenAI(),
            "openai": OpenAI()
        }

    def get_llm(self, temperature, model, streaming):
        return self.llms[self.type].get_llm(temperature=temperature, model=model, streaming=streaming)


def get_chain(temperature, model, prompt):
    """
    Get the conversational chain for the current session.
    Args:
        llm (ChatOpenAI): The OpenAI model to use.
        memory (ConversationBufferWindowMemory): The memory object for the current session.
        prompt (str): The prompt template to use.
    Returns:
        LLMChain: A LLMChain object.
    """
    prompt = PromptTemplate(input_variables=["input", "history"], template=prompt)
    llm = LLMFactory(LLM_TYPE).get_llm(temperature=temperature, model=model, streaming=True)
    chain = prompt | llm
    return chain
