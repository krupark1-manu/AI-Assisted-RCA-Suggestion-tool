import os
import json
import base64
import requests
import httpx
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from backend.ado_client  import get_bug
from config.settings import ADO_ORG, ADO_PROJECT, ADO_PAT, OPENROUTER_API_KEY,EMBEDDING_MODEL

# --- ADO Helpers ---

BASE_URL = f"{ADO_ORG}/{ADO_PROJECT}/_apis"

# Azure DevOps PAT needs base64 encoding for Basic Auth
AUTH_TOKEN = base64.b64encode(f":{ADO_PAT}".encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH_TOKEN}"}

INGESTED_FILE = "data/ingested_ids.json"

if not os.path.exists(INGESTED_FILE):
    os.makedirs("data", exist_ok=True)
    with open(INGESTED_FILE, "w") as f:
        json.dump([], f)

def load_ingested_ids():
    """Load list of already-ingested bug IDs."""
    if os.path.exists(INGESTED_FILE):
        with open(INGESTED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_ingested_ids(ids):
    """Save updated list of ingested IDs."""
    with open(INGESTED_FILE, "w") as f:
        json.dump(list(ids), f)



def query_rca_done_bugs():
    """Query ADO for all bugs tagged 'rcadone'."""
    wiql = {
        "query": """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Bug'
        AND [System.Tags] CONTAINS 'RCA Done'
        ORDER BY [System.CreatedDate] DESC
        """
    }
    url = f"{BASE_URL}/wit/wiql?api-version=7.0"
    r = requests.post(url, headers=HEADERS, json=wiql)
    r.raise_for_status()
    work_items = r.json().get("workItems", [])
    return [wi["id"] for wi in work_items]

# def get_bug_details(bug_id):
#     """Fetch full bug details by ID."""
#     url = f"{BASE_URL}/wit/workitems/{bug_id}?api-version=7.0"
#     r = requests.get(url, headers=HEADERS)
#     r.raise_for_status()
#     return r.json()

# --- Ingestion & Index Building ---

def ingest_new_bugs():
    """Only ingest new RCA Done bugs."""
    existing_ids = load_ingested_ids()
    bug_ids = query_rca_done_bugs()

    new_ids = [bid for bid in bug_ids if bid not in existing_ids]
    if not new_ids:
        print("✅ No new RCA Done bugs found.")
        return
    print(f"📥 Found {len(new_ids)} new bugs to ingest...")

    docs = []

    for bug_id in new_ids:
         bug = get_bug(bug_id)
         fields = bug.get("fields", {})
         title = fields.get("System.Title", "")
         repro = fields.get("Microsoft.VSTS.TCM.ReproSteps", "")
         rca = fields.get("Custom.RCADetail", "")  # Adjust if RCA field is custom
         print(f"RCA details for {bug_id}: {rca}")
         text = f"Title: {title}\nRepro: {repro}\nRCA: {rca}"
         docs.append(Document(page_content=text, metadata={"id": bug_id}))
    
        # --- OpenRouter Embeddings ---
    embeddings = OpenAIEmbeddings(
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=OPENROUTER_API_KEY,
        model=EMBEDDING_MODEL,
        http_client=httpx.Client(verify=False)
    )

    # # # Load existing FAISS index (if exists) or Build FAISS index
    if os.path.exists("data/faiss_index"):
         db = FAISS.load_local("data/faiss_index", embeddings, allow_dangerous_deserialization=True)
         db.add_documents(docs)
         print("✅ Updated existing FAISS index with new bugs.")
    else:
         print("✅ Building python -m backend.ingestion new FAISS index.")
         db = FAISS.from_documents(docs, embeddings)
         print("✅ Built new FAISS index.")

    # # Save index to disk
    os.makedirs("data/faiss_index", exist_ok=True)
    db.save_local("data/faiss_index")

    print(f"Ingested {len(docs)} bugs into FAISS index.")
    save_ingested_ids(existing_ids.union(set(new_ids)))
    print(f"✅ Ingested {len(new_ids)} new bugs and updated FAISS index.")

if __name__ == "__main__":
    ingest_new_bugs()
