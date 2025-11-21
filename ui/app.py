import streamlit as st
from streamlit_lottie import st_lottie
import json
import time
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.suggestion_service import suggest_rca
from config.settings import ADO_PROJECT, ADO_ORG

# -----------------------
# 🎨 Page Configuration
# -----------------------
st.set_page_config(
    page_title="AI RCA Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)
# -----------------------
# 🧩 Utility Functions
# -----------------------
def load_lottiefile(filepath: str):
    """Load lottie animation JSON"""
    with open(filepath, "r") as f:
        return json.load(f)

# You can replace this file with any animation from lottiefiles.com
try:
    bug_anim = load_lottiefile("assets/bug_animation.json")
except:
    bug_anim = None

# -----------------------
# 🎨 Custom CSS Styling
# -----------------------
# --- Load CSS from assets/style.css ---
def load_css(file_path: str):
    with open(file_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/style.css")  # ✅ Load your external stylesheet
# -----------------------
# 🧭 Sidebar Navigation
# -----------------------
st.sidebar.image("assets/logo.png", width=150)
st.sidebar.title("🔧 RCA Assistant")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "🧠 RCA Suggestion", "📊 About App"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tip:** Enter a Bug ID to get RCA suggestions.")
st.sidebar.markdown("⚙️ *Powered by LangChain + OpenRouter*")

# -----------------------
# 🏠 HOME PAGE
# -----------------------
if page == "🏠 Home":
    # col1, col2 = st.columns([1, 2])
    # with col1:
    #     if bug_anim:
    #         st_lottie(bug_anim, height=250, key="bug")
    # with col2:
        st.markdown("## 🧠 Welcome to the AI RCA Assistant")
        st.markdown("""
        This intelligent assistant helps you **predict Root Cause Analysis (RCA)**  
        for newly reported bugs based on historical bug data and fixes.

        **Features:**
        - 🔍 Retrieve similar historical bugs using FAISS vector search  
        - 🤖 Use OpenRouter LLM (e.g., GPT-4) to suggest probable RCA  
        - 💾 Automatically ingest and index new bug data  
        - 🧩 Clean, responsive Streamlit UI  
        """)
        st.success("Ready to assist you! Switch to 'RCA Suggestion' to test.")

# -----------------------
# 🧠 RCA SUGGESTION PAGE
# -----------------------
elif page == "🧠 RCA Suggestion":
    st.markdown("## 🧩 RCA Suggestion Engine")
    st.markdown("Enter a Bug ID below to generate AI-based RCA prediction:")

    bug_id = st.text_input("🔍 Bug ID", placeholder="e.g. 12345")

    if st.button("✨ Generate RCA", use_container_width=True, type="primary"):
        if not bug_id.strip():
            st.warning("⚠️ Please enter a valid bug ID.")
        else:
            with st.spinner("Analyzing similar bugs and generating RCA..."):
                try:
                    time.sleep(1)
                    result = suggest_rca(int(bug_id))

                    st.markdown("### 💬 Chat View")

                    # --- Chat UI Section ---
                    with st.container():
                        st.markdown(
                            f"<div class='chat-box user'><b>User:</b> Please suggest RCA for bug ID "
                            f"<span class='highlight'>{bug_id}</span>.</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"<div class='chat-box assistant'><b>Assistant:</b> {result['suggestion']}</div>",
                            unsafe_allow_html=True
                        )

                    # --- RCA Suggestion Card ---
                    st.markdown("---")
                    st.markdown(
                        f"✅ **Suggested RCA:**\n\n<div class='result-card'>{result['suggestion']}</div>",
                        unsafe_allow_html=True
                    )

                     # === Reference Bugs Section ===
                    st.markdown("## 🗂️ Reference Similar Bugs")

                    if result["reference_message"]:
                        # No similar bugs found
                        st.info(result["reference_message"])
                    else:
                        # Show list of reference IDs + scores
                        for ref in result["references"]:
                            bug_id = ref["bug_id"]
                            score = ref["score"]
                            with st.container():
                                st.markdown(f"""
                            🔗 ADO Bug: [{bug_id}][View in ADO]({ADO_ORG}/{ADO_PROJECT}/_workitems/edit/{bug_id})
                            Similarity Score: `{score:.3f}`
                            ---
                            """)
                            # st.markdown(
                            #     f="""
                            #     <div class='ref-card'>
                            #         🔗 <b>Bug Id:{bug_id}</b>
                            #     </div>
                            #     """,
                            #     unsafe_allow_html=True
                            # )

                     # Reference Bugs
                    # if result["references"]:
                    #     st.markdown("### 🔗 Reference Similar Bugs")
                    #     for ref in result["references"]:
                    #         st.markdown(f"- 🧩 **Bug ID:** {ref}")
                    # elif result["reference_message"]:
                    #     st.info(result["reference_message"])
                        
                    # # --- 🧩 Reference Bugs Section ---
                    # if result.get("references"):
                    #     st.markdown("---")
                    #     st.markdown("### 🧩 Reference RCA-Done Bugs")

                    #     for doc in result["references"]:
                    #         bug_meta = doc.metadata
                    #         bug_id_ref = bug_meta.get("id", "Unknown ID")
                    #         bug_title = doc.page_content.splitlines()[0][:120]  # short title
                    #         st.markdown(
                    #             f"- **Bug #{bug_id_ref}** — {bug_title} "
                    #             f"[🔗 View in ADO]({ADO_ORG}/{ADO_PROJECT}/_workitems/edit/{bug_id_ref})"
                    #         )

                except Exception as e:
                    st.error(f"⚠️ Something went wrong: {str(e)}")


# -----------------------
# 📊 ABOUT PAGE
# -----------------------
elif page == "📊 About App":
    st.markdown("## 🧾 About This App")
    st.markdown("""
    **AI RCA Assistant** uses:
    - 🧠 **LangChain** for document retrieval
    - 🗂 **FAISS** for vector similarity search
    - 🤖 **OpenRouter GPT Models** for RCA generation
    - 🎨 **Streamlit** for front-end UI

    **Workflow:**
    1. Fetches bug details from ADO using `bug_id`
    2. Retrieves similar historical bugs from FAISS index
    3. Sends context + query to LLM via OpenRouter
    4. Displays summarized RCA in human-readable form

    ---
    💡 *Developed for internal RCA prediction & triage automation.*
    """)


