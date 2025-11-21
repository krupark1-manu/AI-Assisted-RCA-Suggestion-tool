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

def suggest_rca(bug_id,threshold=1.0):
    """Given new bug description, suggest RCA based on past bugs."""
    retriever = load_or_build_retriever()
    db = retriever.vectorstore  # get the underlying FAISS DB

     # 1️⃣ Fetch bug details
    bug = get_bug(bug_id)
    fields = bug.get("fields", {})
    title = fields.get("System.Title", "")
    repro = fields.get("Microsoft.VSTS.TCM.ReproSteps", "")
    query = f"Title: {title}\nRepro: {repro}"
    # print(f"🔍 Querying RCA for bug {bug_id}: {query}")
    print(f"🔍 Querying RCA for bug ID: {bug_id}")

    # 2️⃣ Get similar docs + similarity scores
    docs_and_scores = db.similarity_search_with_score(query, k=3)
    
    # # 3️⃣ Retrieve similar docs
    # similar_docs = retriever.invoke(query)
    # 3️⃣ Filter based on similarity threshold
    filtered_docs = []
    for doc, score in docs_and_scores:
        bug_id = doc.metadata.get("id") or doc.metadata.get("bug_id") or None

        print(f"bug_id: {bug_id}, score: {score}")
        # Save metadata + score
        if score <= threshold:      # keep more similar matches
            filtered_docs.append({
                "doc": doc,
                "score": score,
                "bug_id": bug_id
            })
            print(f" after filter bug_id: {bug_id}, score: {score}")

    print("ACTUAL FILTERED DOCS:", [item["bug_id"] for item in filtered_docs])
    # if filtered_docs:
    #     context = "\n\n".join([
    #         f"Bug Title: {doc.metadata.get('title', '')}\n{doc.page_content}"
    #         for doc in filtered_docs
    #     ])
    #     reference_ids = [doc.metadata.get("id", "Unknown") for doc in filtered_docs]
    #     reference_message = None
    # else:
    #     context = "No similar bugs found in historical RCA data."
    #     reference_ids = []
    #     reference_message = "⚠️ No similar bugs found. RCA generated purely from LLM understanding."
    # 3️⃣ Prepare context for LLM
    if filtered_docs:
        context = "\n\n".join([
            f"Bug ID: {item['bug_id']} (Similarity Score: {item['score']})\n"
            f"Bug Title: {item['doc'].metadata.get('title', '')}\n"
            f"{item['doc'].page_content}"
            for item in filtered_docs
        ])

        # reference_ids = [
        #     f"{item['bug_id']} (Score: {item['score']})"
        #     for item in filtered_docs
        # ]
        reference_ids = [
            {
                "bug_id": item["bug_id"],
                "score": float(item["score"])   # convert numpy.float32 → Python float
            }
            for item in filtered_docs
        ]

        reference_message = None

    else:
        context = "No similar bugs found in historical RCA data."
        reference_ids = []
        reference_message = "⚠️ No similar bugs found. RCA generated purely from LLM understanding."


    # 4️⃣ Combine retrieved RCAs into context
    #context = "\n\n".join([doc.page_content for doc in filtered_docs])
    #context = "\n\n".join([f"Bug Title: {doc.metadata.get('title', '')}\n{doc.page_content}" for doc in filtered_docs])

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
    #print(f"💡 Suggested RCA: {response}")

    # ✅ Return both LLM output and reference documents
    return {
        "suggestion": response.content if hasattr(response, "content") else str(response),
        "references": reference_ids,
        "reference_message": reference_message  # send docs back for UI display
    }
    
