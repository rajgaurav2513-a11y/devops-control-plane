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
.logo {
  font-size:32px;
  font-weight:900;
  letter-spacing:1px;
}
.subtitle {
  font-size:14px;
  opacity:0.9;
}

.card {
  background:white;
  padding:20px;
  border-radius:16px;
  border:1px solid var(--border);
  margin-bottom:18px;
}

.section {
  font-size:16px;
  font-weight:800;
  margin-bottom:10px;
}

.stage-ok { background:#E8F5EE; padding:10px; border-radius:8px; }
.stage-warn { background:#FFF4CE; padding:10px; border-radius:8px; }
.stage-block { background:#FDE7E9; padding:10px; border-radius:8px; }

.badge {
  display:inline-block;
  padding:4px 10px;
  border-radius:12px;
  font-size:12px;
  font-weight:700;
}
.badge-dev { background:#E8F5EE; }
.badge-qa { background:#FFF4CE; }
.badge-stage { background:#E6F2FF; }
.badge-prod { background:#FDE7E9; }
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
    exec_id = intent.get("_execution", {}).get("id", str(uuid.uuid4())[:8])
    st.session_state.history.insert(0, {
        "id": exec_id,
        "time": now(),
        "intent": intent,
        "results": results,
    })


# ================= NAV =================
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    if st.button("🧭 Execution"):
        st.session_state.active_tab = "EXECUTION"
with c2:
    if st.button("🌍 Environments"):
        st.session_state.active_tab = "ENV"
with c3:
    if st.button("📉 Drift"):
        st.session_state.active_tab = "DRIFT"
with c4:
    if st.button("📜 History"):
        st.session_state.active_tab = "HISTORY"
with c5:
    if st.button("ℹ️ About"):
        st.session_state.active_tab = "ABOUT"
with c6:
    if st.button("📄 Raw"):
        st.session_state.active_tab = "RAW"

st.markdown("<br>", unsafe_allow_html=True)


# ================= INTENT BUILDER (FIXED POSITION) =================
def build_intent():
    intent = {}

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section">Execution Context</div>', unsafe_allow_html=True)

    env = st.selectbox("Environment", ["dev", "qa", "stage", "prod"])
    exec_mode = st.selectbox("Execution Mode", ["analyze", "auto-deploy"])

    intent["environment"] = env
    intent["execution"] = {"mode": exec_mode}

    # -------- SOURCE --------
    st.markdown('<div class="section">Source</div>', unsafe_allow_html=True)
    src = st.selectbox("Source Type", ["Local Path", "Git Repository"])

    if src == "Local Path":
        intent["application"] = {
            "name": st.text_input("Application Name", "demo-app"),
            "path": st.text_input("Application Path", "./sample-python-app")
        }
    else:
        intent["source"] = {
            "repo": st.text_input("Repo URL"),
            "branch": st.text_input("Branch", "main")
        }

    # -------- CLOUD --------
    st.markdown('<div class="section">Cloud / Platform</div>', unsafe_allow_html=True)
    intent["cloud"] = st.selectbox(
        "Cloud",
        ["aws", "azure", "gcp", "ibm", "oracle", "on-prem"]
    )

    # -------- IMAGE --------
    st.markdown('<div class="section">Image Build & Publish</div>', unsafe_allow_html=True)
    if st.checkbox("Build Image", value=True):
        img = st.text_input("Image Name", "demo-app")
        intent["image"] = {"name": img}

        if st.checkbox("Publish Image"):
            intent["image"]["publish"] = {
                "enabled": True,
                "registry": st.selectbox(
                    "Registry",
                    ["dockerhub", "aws-ecr", "azure-acr", "gcp-gar"]
                ),
                "repository": st.text_input("Target Repository"),
                "tag": st.text_input("Version / Tag", f"{env}-{uuid.uuid4().hex[:6]}")
            }

    # -------- DEPLOY --------
    st.markdown('<div class="section">Deploy</div>', unsafe_allow_html=True)
    deploy = st.selectbox(
        "Deploy Target",
        ["none", "local-docker", "kubernetes", "servers"]
    )
    intent["deploy"] = {"mode": deploy}

    # -------- CONFIG --------
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
                "batch_size": st.number_input("Batch Size", 1, 50, 2),
                "pause_on_failure": True
            }
        }

    st.markdown('</div>', unsafe_allow_html=True)
    return intent


# ================= EXECUTION =================
def execution_view():
    intent = build_intent()

    with st.expander("🔍 View Generated Intent (Advanced)"):
        st.code(yaml.dump(intent, sort_keys=False), language="yaml")

    if st.button("▶ Run Execution", use_container_width=True):
        with st.spinner("Executing decision pipeline..."):
            res = execute(intent)
            res = [r.to_dict() for r in res]
            st.session_state.current_results = res
            st.session_state.current_intent = intent
            save_execution(intent, res)

    if not st.session_state.current_results:
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section">Execution Timeline</div>', unsafe_allow_html=True)

    blocked = False
    for r in st.session_state.current_results:
        if blocked:
            st.markdown(f"<div class='stage-warn'>⏭ {r['stage']} — SKIPPED</div>", unsafe_allow_html=True)
            continue

        if r["status"] == "BLOCKED":
            blocked = True
            st.markdown(f"<div class='stage-block'>❌ {r['stage']} — BLOCKED</div>", unsafe_allow_html=True)
        elif r["status"] == "WARNING":
            st.markdown(f"<div class='stage-warn'>⚠ {r['stage']} — WARNING</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='stage-ok'>✅ {r['stage']} — SUCCESS</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ================= ABOUT =================
def about_view():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section">About ALLDEVOPS</div>', unsafe_allow_html=True)

    st.markdown("""
**ALLDEVOPS** is a **decision-first DevOps control plane**.

It governs deployments, infrastructure, configuration, and Kubernetes
by enforcing **explicit intent, policy checks, and production safety**
before execution.

### Core Principles
• Intent → Analyze → Decide → Execute  
• No blind automation  
• Environment-aware safety  
• Deterministic & explainable  

> _ALLDEVOPS exists to prevent bad production changes before they happen._
""")

    st.markdown('</div>', unsafe_allow_html=True)


# ================= ENV / DRIFT / HISTORY / RAW =================
def env_view():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section">Multi-Environment Overview</div>', unsafe_allow_html=True)

    for env in ["dev", "qa", "stage", "prod"]:
        badge = f"badge-{env}"
        st.markdown(f"<span class='badge {badge}'>{env.upper()}</span>", unsafe_allow_html=True)
        st.caption("Last execution, drift status, policy posture")
        st.divider()

    st.markdown('</div>', unsafe_allow_html=True)


def drift_view():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section">Drift Detection</div>', unsafe_allow_html=True)

    st.info("Decision-first drift detection (no auto-fix).")

    st.checkbox("Infra Drift", value=True)
    st.checkbox("Config Drift", value=True)
    st.checkbox("Kubernetes Drift", value=True)

    if st.button("🔍 Check Drift"):
        st.warning("Drift detected in prod environment")

    st.markdown('</div>', unsafe_allow_html=True)


def history_view():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section">History</div>', unsafe_allow_html=True)

    for h in st.session_state.history:
        with st.expander(f"{h['time']} | version {h['id']}"):
            st.json(h["results"])

    st.markdown('</div>', unsafe_allow_html=True)


def raw_view():
    st.json(st.session_state.current_results)


# ================= RENDER =================
if st.session_state.active_tab == "EXECUTION":
    execution_view()
elif st.session_state.active_tab == "ENV":
    env_view()
elif st.session_state.active_tab == "DRIFT":
    drift_view()
elif st.session_state.active_tab == "HISTORY":
    history_view()
elif st.session_state.active_tab == "ABOUT":
    about_view()
elif st.session_state.active_tab == "RAW":
    raw_view()
