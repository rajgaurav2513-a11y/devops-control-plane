import sys
import os

# Add project root to PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)



import streamlit as st
import yaml
from core.policy.engine import apply_policies
from core.orchestrator.executor import execute

st.set_page_config(page_title="DevOps Control Plane", layout="wide")

st.title("🧠 DevOps Control Plane")
st.caption("Intent → Policy → Safe Execution")

st.divider()

st.subheader("1️⃣ Upload Intent YAML")

uploaded_file = st.file_uploader(
    "Upload your intent YAML file",
    type=["yaml", "yml"]
)

if uploaded_file:
    intent = yaml.safe_load(uploaded_file)

    st.subheader("2️⃣ Parsed Intent")
    st.code(yaml.dump(intent), language="yaml")

    if st.button("🚀 Run Execution"):
        st.subheader("3️⃣ Execution Output")

        safe_intent = apply_policies(intent)
        execute(safe_intent)

        st.success("Execution finished (simulated)")
