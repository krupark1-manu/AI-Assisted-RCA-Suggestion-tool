import os
from dotenv import load_dotenv

load_dotenv()

ADO_ORG = os.getenv("AZURE_DEVOPS_ORG_URL", "https://dev.azure.com/your_org/")
ADO_PROJECT = os.getenv("AZURE_DEVOPS_PROJECT", "your_project")
ADO_PAT = os.getenv("ADO_PAT")  # from env var
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenRouter embedding model
LLM_MODEL = "gpt-4o-mini"  # OpenRouter model
INDEX_PATH="data/faiss_index"