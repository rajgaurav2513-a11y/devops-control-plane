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
  padding:24px;
  border-radius:16px;
  margin-bottom:20px;
}
.logo { font-size:32px; font-weight:900; }
.subtitle { font-size:14px; opacity:0.9; }

.card {
  background:white;
  padding:20px;
  border-radius:16px;
  border:1px solid var(--border);
  margin-bottom:18px;
}

.section { font-size:16px; font-weight:800; margin-bottom:10px; }

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
    Agentic • Intent-Driven • Policy-First DevOps Control Plane
  </div>
</div>
""", unsafe_allow_html=True)


# ================= HELPERS =================
def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def save_execution(intent, results):
    st.session_state.history.insert(0, {
        "id": str(uuid.uuid4())[:8],
        "time": now(),
        "intent": intent,
        "results": results,
    })


# ================= NAV =================
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🧭 Execution"):
        st.session_state.active_tab = "EXECUTION"
with c2:
    if st.button("📉 Drift"):
        st.session_state.active_tab = "DRIFT"
with c3:
    if st.button("📜 History"):
        st.session_state.active_tab = "HISTORY"
with c4:
    if st.button("ℹ️ About"):
        st.session_state.active_tab = "ABOUT"
with c5:
    if st.button("📄 Raw"):
        st.session_state.active_tab = "RAW"


# ================= INTENT BUILDER =================
def build_intent():
    intent = {}

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section">Execution Context</div>', unsafe_allow_html=True)

    env = st.selectbox("Environment", ["dev", "qa", "stage", "prod"])
    exec_mode = st.selectbox("Execution Mode", ["analyze", "auto-deploy"])

    intent["environment"] = env
    intent["execution"] = {"mode": exec_mode}

    # ---------- SOURCE ----------
    st.markdown('<div class="section">Source</div>', unsafe_allow_html=True)
    src = st.selectbox("Source Type", ["Local Path", "Git Repository"])

    if src == "Local Path":
        intent["application"] = {
            "name": "demo-app",
            "path": st.text_input("Application Path", "./sample-python-app")
        }
    else:
        intent["application"] = {
            "name": "demo-app",
            "repo": st.text_input("Repo URL"),
            "branch": st.text_input("Branch", "main")
        }

    # ---------- IMAGE ----------
    st.markdown('<div class="section">Image Build</div>', unsafe_allow_html=True)
    if st.checkbox("Build Image"):
        intent["image"] = {
            "name": st.text_input("Image Name", "demo-app")
        }

    # ---------- INFRA ----------
    st.markdown('<div class="section">Infrastructure</div>', unsafe_allow_html=True)
    if st.checkbox("Enable Infrastructure"):
        intent["infrastructure"] = {
            "tool": "terraform",
            "mode": "plan",
            "auto_apply": False,
            "risk": {
                "public": st.checkbox("Detect Public Exposure", True),
                "cost": st.checkbox("Detect Cost Risk", True),
                "blast": st.checkbox("Detect Blast Radius", True),
            }
        }

    # ---------- CONFIG ----------
    st.markdown('<div class="section">Config Management</div>', unsafe_allow_html=True)
    if st.checkbox("Apply Configuration"):
        intent["config"] = {
            "targets": {
                "hosts": st.text_area(
                    "Hosts (one per line)",
                    "10.0.1.12\n10.0.1.13"
                ).splitlines()
            },
            "connection": {
                "user": st.text_input("SSH User", "ubuntu"),
                "key_path": st.text_input("SSH Key Path", "~/.ssh/id_rsa")
            },
            "rollout": {
                "batch_size": st.number_input("Batch Size", 1, 20, 2),
                "pause_on_failure": True,
                "rollback_on_failure": True
            }
        }

    # ---------- TESTING ----------
    st.markdown('<div class="section">Testing</div>', unsafe_allow_html=True)

    if st.checkbox("Enable Testing"):
        test_type = st.selectbox(
            "Test Type",
            ["smoke", "api", "selenium", "performance"]
        )

        intent["testing"] = {
            "enabled": True,
            "type": test_type,
            "target": st.text_input("Target URL", "http://localhost:8080")
        }

        if test_type == "smoke":
            intent["testing"]["checks"] = [
                {"type": "http", "path": "/health", "expect": 200}
            ]

        if test_type == "api":
            intent["testing"]["api"] = [
                {"path": "/health", "method": "GET", "expect_status": 200}
            ]

        if test_type == "selenium":
            intent["testing"]["ui"] = [
                {"open": "/"},
                {"expect_text": "Welcome"}
            ]

        if test_type == "performance":
            intent["testing"]["performance"] = {
                "users": st.number_input("Virtual Users", 10, 1000, 50),
                "duration": st.text_input("Duration", "1m")
            }

    # ---------- DEPLOY ----------
    st.markdown('<div class="section">Deploy</div>', unsafe_allow_html=True)
    intent["deploy"] = {
        "mode": st.selectbox("Deploy Mode", ["none", "local-docker"])
    }

    st.markdown('</div>', unsafe_allow_html=True)
    return intent


# ================= EXECUTION VIEW =================
def execution_view():
    intent = build_intent()

    with st.expander("🔍 View Generated Intent"):
        st.code(yaml.dump(intent, sort_keys=False), language="yaml")

    if st.button("▶ Run Execution", use_container_width=True):
        res = execute(intent)
        res = [r.to_dict() for r in res]
        st.session_state.current_results = res
        save_execution(intent, res)

    if not st.session_state.current_results:
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section">Execution Timeline</div>', unsafe_allow_html=True)

    blocked = False
    for r in st.session_state.current_results:
        stage = r["stage"]
        status = r["status"]
        msg = r.get("message", "")

        if blocked or status == "SKIPPED":
            st.markdown(f"<div class='stage-warn'>⏭ {stage} — SKIPPED</div>", unsafe_allow_html=True)
        elif status == "BLOCKED":
            blocked = True
            st.markdown(f"<div class='stage-block'>❌ {stage} — {msg}</div>", unsafe_allow_html=True)
        elif status == "WARNING":
            st.markdown(f"<div class='stage-warn'>⚠ {stage} — {msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='stage-ok'>✅ {stage}</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ================= OTHER VIEWS =================
def history_view():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    for h in st.session_state.history:
        with st.expander(f"{h['time']} | {h['id']}"):
            st.json(h["results"])
    st.markdown('</div>', unsafe_allow_html=True)


def about_view():
    st.markdown('<div class="card">ALLDEVOPS – Decision-first DevOps control plane</div>', unsafe_allow_html=True)


def raw_view():
    st.json(st.session_state.current_results)


# ================= ROUTER =================
if st.session_state.active_tab == "EXECUTION":
    execution_view()
elif st.session_state.active_tab == "HISTORY":
    history_view()
elif st.session_state.active_tab == "ABOUT":
    about_view()
elif st.session_state.active_tab == "RAW":
    raw_view()
