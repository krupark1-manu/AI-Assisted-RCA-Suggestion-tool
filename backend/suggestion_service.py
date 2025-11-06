import os,httpx
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableMap, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from backend import ingestion
from backend.ado_client import get_bug
from backend.retriever import build_retriever
from config.settings import OPENROUTER_API_KEY, LLM_MODEL,INDEX_PATH

def load_or_build_retriever():
    """Load FAISS retriever, or build if index is missing."""
    if not os.path.exists(INDEX_PATH):
        print("⚠️ FAISS index not found. Running ingestion...")
        ingestion.ingest_new_bugs()

    return build_retriever()

def suggest_rca(bug_id):
    """Given new bug description, suggest RCA based on past bugs."""
    retriever = load_or_build_retriever()

     # 1️⃣ Fetch bug details
    bug = get_bug(bug_id)
    fields = bug.get("fields", {})
    title = fields.get("System.Title", "")
    repro = fields.get("Microsoft.VSTS.TCM.ReproSteps", "")
    query = f"Title: {title}\nRepro: {repro}"
    print(f"🔍 Querying RCA for bug {bug_id}: {query}")

     # 3️⃣ Retrieve similar docs
    similar_docs = retriever.invoke(query)

    # 4️⃣ Combine retrieved RCAs into context
    context = "\n\n".join([doc.page_content for doc in similar_docs])

     # ✅ Initialize LLM (OpenRouter)
    llm = ChatOpenAI(
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=OPENROUTER_API_KEY,
        model=LLM_MODEL,
        temperature=0.3,
        http_client=httpx.Client(verify=False)
    )

     # Prompt Template
    prompt = ChatPromptTemplate.from_template("""
    You are an expert software engineer who provides RCA (Root Cause Analysis) suggestions
    based on past resolved bugs.

    --- New Bug ---
    {query}

    --- Similar Past RCA Context ---
    {context}

    Suggest the most likely RCA for the above bug in a clear, concise way.
    """)

    # Build Retrieval Chain (modern version)
     # ✅ LCEL retrieval chain
    chain = (
        RunnableMap({
            "context": RunnablePassthrough(),
            "query": RunnablePassthrough(),
        })
        | prompt
        | llm
    )

     # ✅ Run the chain
    response = chain.invoke({"query": query, "context": context})
    print(f"💡 Suggested RCA: {response}")

    # ✅ Return LLM’s text output
    return response.content if hasattr(response, "content") else str(response)
    
