import streamlit as st
import yaml

from core.orchestrator.executor import execute
from core.models.result import Status

st.set_page_config(page_title="Agentic DevOps Control Plane", layout="wide")
st.title("🧠 Agentic DevOps Control Plane (V1)")

st.subheader("📄 Intent Input")

intent_text = st.text_area(
    "Paste intent YAML here",
    height=300,
)

if not intent_text:
    st.stop()

try:
    intent = yaml.safe_load(intent_text)
except Exception as e:
    st.error(f"Invalid YAML: {e}")
    st.stop()

if st.button("▶️ Run Execution"):
    with st.spinner("Executing agentic pipeline..."):
        results = execute(intent)

    st.subheader("📊 Execution Results")

    for r in results:
        # ---- SAFE STATUS HANDLING ----
        status = r.status
        if isinstance(status, Status):
            status_value = status.value
        else:
            status_value = str(status)

        color = {
            "SUCCESS": "green",
            "WARNING": "orange",
            "WARN": "orange",
            "BLOCKED": "red",
            "FAILED": "red",
            "SKIPPED": "gray",
        }.get(status_value, "blue")

        st.markdown(f"### {r.stage} — :{color}[{status_value}]")
        st.write(r.message)

        for log in r.logs:
            st.code(log)
