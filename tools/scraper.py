import requests
from bs4 import BeautifulSoup
from langchain.prompts import PromptTemplate
from config import LLM_TYPE
from source.chain import LLMFactory

def summarize_content(content, query):
    # Initialize the OpenAI model
    llm = LLMFactory(LLM_TYPE).get_llm()
    # Define the prompt template for summarization
    prompt_template = PromptTemplate(
        input_variables=["text","query"],
        template="""Please summarize the following text:
        {text}
        extract the most relevant and important information from the text related to the following user question:
        {query}
        Summary:
        """
    )
    # Create the LLMChain for summarization
    chain = prompt_template | llm
    # Generate the summary
    summary = chain.invoke({"text": content, "query": query})
    return summary.content

def scrape_websites(url_list, query):
    scraped_content = ""

    for url in url_list:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check if the request was successful
            soup = BeautifulSoup(response.content, 'lxml')
            text = soup.get_text(separator=' ', strip=True)
            scraped_content += f"Data from {url}: {text}\n"
        except requests.exceptions.RequestException as e:
            print(f"Error scraping {url}: {e}")
            scraped_content += f"Error scraping {url}: {e}\n"
    summarized_content = summarize_content(text, query)
    return summarized_content

