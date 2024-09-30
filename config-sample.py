POSTGRES_URL = "postgresql://username:password@host_ip:port/database_name"
SQLITE_URL = "sqlite:///hackgpt_convo.db"  # or "sqlite:///<.db file path>"
OPENAI_API_KEY = ""

# For AzureOpenAI
# ------------------------------------
AZURE_OPENAI_API_KEY = ""
AZURE_OPENAI_ENDPOINT = ""
AZURE_DEPLOYMENT = ""
API_VERSION = ""

# Which LLM to use
# ------------------------------------
# openai = OpenAI ChatGPT
# azure = Azure OpenAI
LLM_TYPE = "openai"  # or "azure"
DB_TYPE = "postgres"  # or "postgres"

if DB_TYPE == "postgres":
    DATABASE_URL = POSTGRES_URL
elif DB_TYPE == "sqlite":
    DATABASE_URL = SQLITE_URL

import os 
if DB_TYPE == "sqlite":
    if not os.path.exists("hackgpt_convo.db"):
        open("hackgpt_convo.db", "w").close()