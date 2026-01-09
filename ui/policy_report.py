import streamlit as st


def render_policy_report(policy_result: dict):
    st.subheader("🛡 Policy Decision")

    status = policy_result.get("status")
    report = policy_result.get("policy_report", {})

    total = report.get("total_policies", 0)
    triggered = report.get("triggered", [])
    blocked = report.get("blocked", False)

    # -----------------------
    # Decision Header
    # -----------------------
    if status == "BLOCKED":
        st.error("❌ DECISION: BLOCKED")
        st.write("Execution stopped due to policy violation.")
    elif status == "WARNING":
        st.warning("⚠ DECISION: WARNING")
        st.write("Execution continued with warnings.")
    else:
        st.success("✅ DECISION: ALLOW")
        st.write("No policy violations detected.")

    st.markdown(f"""
    **Triggered Policies:** {len(triggered)}  
    **Total Policies Evaluated:** {total}  
    **Blocking Policy Triggered:** {"Yes" if blocked else "No"}
    """)

    st.divider()

    # -----------------------
    # Triggered Policies Table
    # -----------------------
    st.subheader("Triggered Policies")

    if not triggered:
        st.info("No policies were triggered.")
        return

    table_data = []
    for p in triggered:
        impact = "Execution stopped" if p["action"] == "BLOCK" else "Execution continued"
        table_data.append({
            "Policy ID": p["policy_id"],
            "Action": p["action"],
            "Message": p["message"],
            "Impact": impact
        })

    st.table(table_data)
