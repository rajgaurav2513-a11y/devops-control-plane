import streamlit as st
from core.models.result import Status


def approval_gate(results: list) -> bool:
    blocking = [r for r in results if r.status == Status.BLOCKED]
    warnings = [r for r in results if r.status in (Status.WARN, Status.WARNING)]

    if blocking:
        st.error("❌ Deployment BLOCKED")
        return False

    if warnings:
        st.warning("⚠️ Warnings detected")
        return st.button("Approve Deployment")

    st.success("✅ Auto-approved")
    return True
