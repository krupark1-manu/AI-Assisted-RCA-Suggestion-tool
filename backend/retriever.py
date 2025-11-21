import httpx
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from config.settings import OPENROUTER_API_KEY, EMBEDDING_MODEL, INDEX_PATH


def build_retriever():
    """Load FAISS index and return retriever using OpenRouter embeddings."""
    embeddings = OpenAIEmbeddings(
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=OPENROUTER_API_KEY,
        model=EMBEDDING_MODEL,
        http_client=httpx.Client(verify=False)
    )
    # ⚠️ add allow_dangerous_deserialization=True to avoid errors with FAISS.load_local
    db = FAISS.load_local(
        INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    
    # ✅ Limit the number of documents retrieved
    return db.as_retriever(search_type="similarity", search_kwargs={"k": 3})   


