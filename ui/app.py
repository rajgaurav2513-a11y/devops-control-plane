# ui/app.py
# 🔧 FINAL — STATE-SAFE, REFRESH-SAFE, RESUME-SAFE

import streamlit as st
import yaml
import hashlib

from core.orchestrator.executor import execute
from core.models.result import Status


st.set_page_config(
    page_title="Agentic DevOps Control Plane",
    layout="wide",
)

st.title("🧠 Agentic DevOps Control Plane")

# -----------------------------
# SESSION STATE (CRITICAL)
# -----------------------------
if "execution_id" not in st.session_state:
    st.session_state.execution_id = None

if "last_results" not in st.session_state:
    st.session_state.last_results = []

if "last_intent_hash" not in st.session_state:
    st.session_state.last_intent_hash = None


# -----------------------------
# INTENT INPUT
# -----------------------------
st.subheader("📄 Intent Input")

intent_text = st.text_area(
    "Paste intent YAML here",
    height=300,
)

if not intent_text.strip():
    st.stop()

# 🔑 Detect NEW intent (THIS FIXES THE BUG)
current_hash = hashlib.sha256(intent_text.encode()).hexdigest()

if st.session_state.last_intent_hash != current_hash:
    # New intent → fresh execution
    st.session_state.execution_id = None
    st.session_state.last_results = []
    st.session_state.last_intent_hash = current_hash

intent = yaml.safe_load(intent_text)


# -----------------------------
# RUN EXECUTION
# -----------------------------
if st.button("▶️ Run Execution"):
    # Resume ONLY if same intent
    if st.session_state.execution_id:
        intent["_execution"] = {
            "id": st.session_state.execution_id
        }

    with st.spinner("Executing decision plane..."):
        results = execute(intent)

    # Persist execution_id for resume
    exec_id = intent.get("_execution", {}).get("id")
    if exec_id:
        st.session_state.execution_id = exec_id

    st.session_state.last_results = results


# -----------------------------
# RESULTS
# -----------------------------
if st.session_state.last_results:
    st.subheader("📊 Execution Results")

    for r in st.session_state.last_results:
        status = r.status.value if isinstance(r.status, Status) else str(r.status)

        color = {
            "SUCCESS": "green",
            "WARNING": "orange",
            "BLOCKED": "red",
            "SKIPPED": "gray",
        }.get(status, "blue")

        st.markdown(f"### {r.stage} — :{color}[{status}]")
        st.write(r.message)

        for log in r.logs or []:
            st.code(log)


# ❌ Approval gate intentionally disabled
