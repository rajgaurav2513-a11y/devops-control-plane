# ui/app.py
# 🔧 FULL FILE WITH FINAL RESUME + VISIBILITY FIX (COPY–PASTE)

import streamlit as st
import yaml

from core.orchestrator.executor import execute
from core.models.result import Status
from ui.approval_gate import render_approval_gate


st.set_page_config(
    page_title="Agentic DevOps Control Plane",
    layout="wide",
)

st.title("🧠 Agentic DevOps Control Plane")

if "execution_id" not in st.session_state:
    st.session_state.execution_id = None

if "last_results" not in st.session_state:
    st.session_state.last_results = []


st.subheader("📄 Intent Input")

intent_text = st.text_area(
    "Paste intent YAML here",
    height=300,
)

if not intent_text.strip():
    st.stop()

intent = yaml.safe_load(intent_text)

if st.button("▶️ Run Execution"):
    if st.session_state.execution_id:
        intent["_execution"] = {
            "id": st.session_state.execution_id
        }

    st.session_state.last_results = []

    with st.spinner("Executing decision plane..."):
        results = execute(intent)

    st.session_state.execution_id = intent["_execution"]["id"]
    st.session_state.last_results = results


if st.session_state.last_results:
    st.subheader("📊 Execution Results")

    for r in st.session_state.last_results:
        status = r.status.value if isinstance(r.status, Status) else str(r.status)

        color = {
            "SUCCESS": "green",
            "BLOCKED": "red",
            "SKIPPED": "gray",
        }.get(status, "blue")

        st.markdown(f"### {r.stage} — :{color}[{status}]")
        st.write(r.message)

        for log in r.logs:
            st.code(log)


if st.session_state.execution_id:
    render_approval_gate(st.session_state.execution_id)
    st.info(f"Execution ID: `{st.session_state.execution_id}`")
