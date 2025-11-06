# AI-Assisted RCA App

## Overview
This project is a hackathon-ready prototype of an **AI-Assisted Root Cause Analysis (RCA) suggestion tool** that integrates with Azure DevOps (ADO). The app pulls bugs tagged with `rcadone` from ADO, builds a vector index (RAG), and suggests RCA/fix for new bugs based on historical RCA-done bugs.

The project is built with:
- **Python** backend
- **Streamlit** frontend
- **LangChain / LlamaIndex** for RAG
- **FAISS** vector store
- **OpenAI/OpenRouter API for embeddings / LLMs**

---

## Folder Structure
```
ai_rca_app/
├── backend/                     # Backend logic
│   ├── __init__.py
│   ├── ado_client.py            # ADO API calls
│   ├── ingestion.py             # Pull historical bugs, build FAISS
│   ├── retriever.py             # Load FAISS retriever
│   └── suggestion_service.py    # Suggest RCA for new bugs
├── ui/                          # Streamlit frontend
│   └── app.py
├── config/                      # Config files
│   ├── __init__.py
│   └── settings.py              # ADO and OpenAI config
├── data/                        # Store FAISS index or temporary data
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## Setup Instructions

### 1. Clone repo & create virtual environment
```bash
git clone <repo_url>
cd AIAssistedRCA
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variables
Create a `.env` file or set OS environment variables:
```
ADO_ORG=your-org
ADO_PROJECT=your-project
ADO_PAT=your-pat-token
OPENAI_API_KEY=your-openai-api-key/OPENROUTER_API_KEY=your-openrouter-api-key
```

### 4. Ingest ADO Bugs
```bash
python backend/ingestion.py
```
- Pulls all bugs tagged `rcadone` from ADO
- Builds FAISS index stored in `data/faiss_index/`

### 5. Run the Streamlit UI
```bash
streamlit run ui/app.py
```
- Enter a new **Bug ID** in the UI
- The app fetches bug details and suggests RCA/fix based on historical RCA-done bugs

---

## How It Works
1. **Ingestion**: Pull historical bugs from ADO with tag `rcadone` → build FAISS vector store.
2. **Retriever**: Load FAISS index and embed text using OpenAI embeddings.
3. **RCA Suggestion**: User enters new bug ID → fetches bug details from ADO → query retriever → LLM synthesizes suggestion.
4. **UI**: Streamlit interface displays suggested RCA/fix.

---

## Notes
- WIQL `CONTAINS` is **case-insensitive** but **spacing matters** in tags.
- For multiple tag variants (e.g., `RCA-Done`, `RCA_Done`), update WIQL query accordingly.
- FAISS index rebuild required when new RCA-done bugs are added.

---

## Future Enhancements
- Multi-agent support (RCA agent, fix suggestion agent)
- Automatic ingestion on a schedule / webhook trigger
- Feedback loop to improve suggestion accuracy
- Integration with other tools (Slack, Teams, Jira)

---

## References
- [Azure DevOps REST API](https://learn.microsoft.com/en-us/rest/api/azure/devops/)
- [LangChain Documentation](https://www.langchain.com/docs/)
- [FAISS Vector Store](https://github.com/facebookresearch/faiss)


