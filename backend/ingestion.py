import os
import numpy as np
import json
import base64
import requests
import httpx
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from backend.ado_client  import get_bug
from config.settings import ADO_ORG, ADO_PROJECT, ADO_PAT, OPENROUTER_API_KEY,EMBEDDING_MODEL,INDEX_PATH

# --- ADO Helpers ---

BASE_URL = f"{ADO_ORG}/{ADO_PROJECT}/_apis"

# Azure DevOps PAT needs base64 encoding for Basic Auth
AUTH_TOKEN = base64.b64encode(f":{ADO_PAT}".encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH_TOKEN}"}

INGESTED_FILE = "data/ingested_ids.json"

# --------- Manual L2 Normalization ----------
def normalize(vec):
    vec = np.array(vec)
    norm = np.linalg.norm(vec)
    return vec / norm if norm != 0 else vec

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
         docs.append(Document(page_content=text, metadata={"id": bug_id, "title": title}))
    
        # --- OpenRouter Embeddings ---
    embeddings = OpenAIEmbeddings(
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=OPENROUTER_API_KEY,
        model=EMBEDDING_MODEL,
        http_client=httpx.Client(verify=False)
    )
    texts = [d.page_content for d in docs]
    metadatas = [d.metadata for d in docs]

    raw_vectors = embeddings.embed_documents(texts)
    normalized_vectors = [normalize(v) for v in raw_vectors]   # ⭐ Manual L2 normalization

    # # # Load existing FAISS index (if exists) or Build FAISS index
    if os.path.exists(INDEX_PATH):
         db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
         db.add_documents(docs)
        #  db.add_embeddings(
        #     embeddings=normalized_vectors,
        #     texts=texts,
        #     metadatas=metadatas
        # )
         print("✅ Updated existing FAISS index with new bugs.")
    else:
         print("✅ Building python -m backend.ingestion new FAISS index.")
         db = FAISS.from_documents(docs, embeddings)
         # Build new index correctly: need list of (text, vector) pairs
         #text_embedding_pairs = list(zip(texts, normalized_vectors))
        #  text_embedding_pairs = [(texts[i], normalized_vectors[i]) for i in range(len(texts))]
        #  db = FAISS.from_embeddings(
        #     text_embeddings=text_embedding_pairs,
        #     embedding=embeddings,
        #     metadatas=metadatas
        #)
         print("✅ Built new FAISS index.")

    # # Save index to disk
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    db.save_local(INDEX_PATH)

    print(f"Ingested {len(docs)} bugs into FAISS index.")
    save_ingested_ids(existing_ids.union(set(new_ids)))
    print(f"✅ Ingested {len(new_ids)} new bugs and updated FAISS index.")

if __name__ == "__main__":
    ingest_new_bugs()
