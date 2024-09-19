from langchain_core.prompts.prompt import PromptTemplate
from langchain_openai import ChatOpenAI


def get_llm(temperature, model):
    """
    Get the LLM for the current session.
    Args:
        llm (ChatOpenAI): The OpenAI model to use.
    Returns:
        LLMChain: A LLMChain object.
    """
    return ChatOpenAI(temperature=temperature, model=model, streaming=True)


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
    llm = get_llm(temperature, model)
    chain = prompt | llm
    return chain
