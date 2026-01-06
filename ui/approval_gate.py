import streamlit as st
from datetime import datetime

from core.approval.store import load as load_approval, save as save_approval
from core.approval.model import ApprovalStatus


def render_approval_gate(execution_id: str):
    approval = load_approval(execution_id)
    if not approval:
        return

    st.markdown("---")
    st.subheader("🛂 Approval Gate")
    st.info(f"Current status: **{approval.status}**")

    if approval.status in (ApprovalStatus.PENDING, ApprovalStatus.HELD):
        col1, col2, col3 = st.columns(3)

        if col1.button("✅ Approve"):
            approval.status = ApprovalStatus.APPROVED
            approval.decided_at = datetime.utcnow()
            save_approval(approval)
            st.rerun()

        if col2.button("❌ Reject"):
            approval.status = ApprovalStatus.REJECTED
            approval.decided_at = datetime.utcnow()
            save_approval(approval)
            st.rerun()

        if col3.button("⏸ Hold"):
            approval.status = ApprovalStatus.HELD
            save_approval(approval)
            st.rerun()

    elif approval.status == ApprovalStatus.APPROVED:
        st.success("Approved. Click Run Execution to continue.")

    elif approval.status == ApprovalStatus.REJECTED:
        st.error("Execution rejected. This is final.")
