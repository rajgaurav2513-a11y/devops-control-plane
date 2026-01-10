import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import yaml
import uuid
import datetime

from core.orchestrator.executor import execute


# ================= SESSION =================
if "history" not in st.session_state:
    st.session_state.history = []

if "current_results" not in st.session_state:
    st.session_state.current_results = None

if "current_intent" not in st.session_state:
    st.session_state.current_intent = None

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "EXECUTION"


# ================= PAGE =================
st.set_page_config(layout="wide", page_title="ALLDEVOPS | Control Plane")


# ================= STYLE =================
st.markdown("""
<style>
:root {
  --blue:#0F6CBD;
  --dark:#0B3C5D;
  --bg:#F4F7FB;
  --border:#E1E6EF;
}
.stApp { background: var(--bg); }

.header {
  background: linear-gradient(90deg, var(--blue), var(--dark));
  color:white;
  padding:20px;
  border-radius:12px;
  margin-bottom:16px;
}
.logo {
  font-size:28px;
  font-weight:800;
}
.subtitle {
  font-size:13px;
  opacity:0.9;
}

.card {
  background:white;
  padding:16px;
  border-radius:12px;
  border:1px solid var(--border);
  margin-bottom:14px;
}

.nav button {
  width:100%;
  border-radius:8px;
  font-weight:600;
}

.stage-ok { background:#E8F5EE; padding:10px; border-radius:8px; }
.stage-warn { background:#FFF4CE; padding:10px; border-radius:8px; }
.stage-block { background:#FDE7E9; padding:10px; border-radius:8px; }
</style>
""", unsafe_allow_html=True)


# ================= HEADER =================
st.markdown("""
<div class="header">
  <div class="logo">🚀 ALLDEVOPS</div>
  <div class="subtitle">
    Intent-Driven • Policy-First • Decision-Centric DevOps
  </div>
</div>
""", unsafe_allow_html=True)


# ================= HELPERS =================
def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def save_execution(intent, results):
    exec_id = intent.get("_execution", {}).get("id", str(uuid.uuid4())[:8])
    st.session_state.history.insert(0, {
        "id": exec_id,
        "time": now(),
        "intent": intent,
        "results": results,
    })


# ================= NAV =================
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("📝 Execution"):
        st.session_state.active_tab = "EXECUTION"

with c2:
    if st.button("📜 History"):
        st.session_state.active_tab = "HISTORY"

with c3:
    if st.button("🛡 Policy"):
        st.session_state.active_tab = "POLICY"

with c4:
    if st.button("📄 Raw"):
        st.session_state.active_tab = "RAW"


st.markdown("<br>", unsafe_allow_html=True)


# ================= EXECUTION (INTENT + TIMELINE) =================
def execution_view():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Intent")

    default_intent = {
        "execution": {"mode": "analyze"},
        "environment": "dev",
        "application": {
            "name": "demo-app",
            "path": "./sample-python-app"
        },
        "deploy": {"mode": "docker"},
        "policies": []
    }

    text = st.text_area(
        "Intent (YAML)",
        yaml.dump(st.session_state.current_intent or default_intent, sort_keys=False),
        height=320
    )

    try:
        intent = yaml.safe_load(text)

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("▶ Run", use_container_width=True):
                with st.spinner("Executing decision pipeline..."):
                    res = execute(intent)
                    res = [r.to_dict() for r in res]
                    st.session_state.current_results = res
                    st.session_state.current_intent = intent
                    save_execution(intent, res)

        with col2:
            st.success("Intent validated")

    except Exception as e:
        st.error(str(e))

    st.markdown('</div>', unsafe_allow_html=True)

    # -------- TIMELINE --------
    if not st.session_state.current_results:
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Timeline")

    blocked = False
    for r in st.session_state.current_results:
        stage = r["stage"]
        status = r["status"]

        if blocked:
            st.markdown(f"<div class='stage-warn'>⏭ {stage} — SKIPPED</div>", unsafe_allow_html=True)
            continue

        if status == "BLOCKED":
            blocked = True
            st.markdown(f"<div class='stage-block'>❌ {stage} — BLOCKED</div>", unsafe_allow_html=True)
        elif status == "WARNING":
            st.markdown(f"<div class='stage-warn'>⚠ {stage} — WARNING</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='stage-ok'>✅ {stage} — SUCCESS</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ================= POLICY =================
def policy_view():
    if not st.session_state.current_results:
        st.info("No execution yet.")
        return

    p = next((r for r in st.session_state.current_results if r["stage"] == "POLICY"), None)
    if not p:
        st.info("No policy stage.")
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Policy Decision")

    if p["status"] == "BLOCKED":
        st.error("❌ BLOCKED")
    elif p["status"] == "WARNING":
        st.warning("⚠ WARNING")
    else:
        st.success("✅ ALLOW")

    for t in p.get("policy_report", {}).get("triggered", []):
        st.write(f"- {t['action']} | {t['policy_id']} — {t['message']}")

    st.markdown('</div>', unsafe_allow_html=True)


# ================= HISTORY (REDEPLOY ENABLED) =================
def history_view():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("History")

    for h in st.session_state.history:
        with st.expander(f"{h['time']} | version: {h['id']}"):
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"🔁 Re-Analyze {h['id']}"):
                    st.session_state.current_intent = h["intent"]
                    st.session_state.current_results = None
                    st.session_state.active_tab = "EXECUTION"

            with col2:
                if st.button(f"🚀 Re-Deploy {h['id']}"):
                    intent = dict(h["intent"])
                    intent["execution"] = {"mode": "auto-deploy"}
                    res = execute(intent)
                    st.session_state.current_results = [r.to_dict() for r in res]
                    st.session_state.current_intent = intent
                    save_execution(intent, st.session_state.current_results)
                    st.session_state.active_tab = "EXECUTION"

            st.json(h["results"])

    st.markdown('</div>', unsafe_allow_html=True)


# ================= RAW =================
def raw_view():
    st.json(st.session_state.current_results)


# ================= RENDER =================
if st.session_state.active_tab == "EXECUTION":
    execution_view()
elif st.session_state.active_tab == "HISTORY":
    history_view()
elif st.session_state.active_tab == "POLICY":
    policy_view()
elif st.session_state.active_tab == "RAW":
    raw_view()
