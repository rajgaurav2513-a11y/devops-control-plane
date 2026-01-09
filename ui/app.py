import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import yaml
import uuid
import datetime

from core.orchestrator.executor import execute


# -------------------- SESSION --------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "current_results" not in st.session_state:
    st.session_state.current_results = None

if "current_intent" not in st.session_state:
    st.session_state.current_intent = None


# -------------------- STYLE --------------------
st.set_page_config(layout="wide")
st.markdown("""
<style>
:root { --blue:#0078D4; --bg:#F5F7FB; }
.stApp { background: var(--bg); }
.header { background: var(--blue); color:white; padding:14px 18px; border-radius:8px; }
.card { background:white; padding:14px; border-radius:8px; border:1px solid #E5EAF0; margin-bottom:10px; }
.badge-ok { color:#107C10; font-weight:600; }
.badge-warn { color:#D83B01; font-weight:600; }
.badge-block { color:#A4262C; font-weight:700; }
.btn-primary button { background:#0078D4; color:white; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><h2>Agentic / Intent-Driven DevOps Control Plane</h2></div>', unsafe_allow_html=True)


# -------------------- HELPERS --------------------
def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def save_execution(intent, results):
    st.session_state.history.insert(0, {
        "id": str(uuid.uuid4())[:8],
        "time": now(),
        "intent": intent,
        "results": results
    })


# -------------------- UI PARTS --------------------
def start_execution():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Start New Execution")
    if st.button("➕ New Execution", use_container_width=True):
        st.session_state.current_intent = None
        st.session_state.current_results = None
        st.success("New execution started. Go to Intent tab.")
    st.markdown('</div>', unsafe_allow_html=True)


def intent_editor():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Intent Editor")

    default_intent = {
        "execution": {"mode": "analyze"},
        "tests": {"enabled": False},
        "application": {"name": "demo-app", "path": "./sample-python-app"},
        "run": {"command": ["python", "app.py"]},
        "deploy": {"mode": "local"},
        "policies": [
            {
                "id": "block-without-tests",
                "when": {"tests.enabled": False},
                "action": "BLOCK",
                "message": "Tests are mandatory"
            }
        ]
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
                with st.spinner("Executing..."):
                    res = execute(intent)
                    res = [r.to_dict() for r in res]
                    st.session_state.current_results = res
                    st.session_state.current_intent = intent
                    save_execution(intent, res)
        with col2:
            st.success("Intent valid")
    except Exception as e:
        st.error(e)

    st.markdown('</div>', unsafe_allow_html=True)


def timeline():
    if not st.session_state.current_results:
        st.info("No execution yet.")
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Execution Timeline")

    icons = {"SUCCESS":"✅","WARNING":"⚠️","BLOCKED":"❌","SKIPPED":"⏭️"}
    blocked = False

    for r in st.session_state.current_results:
        if blocked:
            st.write("⏭️", r["stage"], "— SKIPPED")
            continue

        s = r["status"]
        icon = icons.get(s,"ℹ️")
        if s == "BLOCKED":
            blocked = True
            st.error(f"{icon} {r['stage']} — BLOCKED")
        elif s == "WARNING":
            st.warning(f"{icon} {r['stage']} — WARNING")
        else:
            st.success(f"{icon} {r['stage']} — SUCCESS")

    st.markdown('</div>', unsafe_allow_html=True)


def policy():
    if not st.session_state.current_results:
        st.info("No execution yet.")
        return

    p = next((r for r in st.session_state.current_results if r["stage"]=="POLICY"), None)
    if not p:
        st.info("No policy stage.")
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Policy Decision")

    if p["status"]=="BLOCKED":
        st.markdown('<span class="badge-block">BLOCKED</span>', unsafe_allow_html=True)
    elif p["status"]=="WARNING":
        st.markdown('<span class="badge-warn">WARNING</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-ok">ALLOW</span>', unsafe_allow_html=True)

    report = p.get("policy_report",{})
    for t in report.get("triggered",[]):
        if t["action"]=="BLOCK":
            st.error(f"❌ {t['policy_id']}: {t['message']}")
        else:
            st.warning(f"⚠ {t['policy_id']}: {t['message']}")

    if not report.get("triggered"):
        st.success("No policies triggered")

    st.markdown('</div>', unsafe_allow_html=True)


def history():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("History & Rollback")

    for h in st.session_state.history:
        with st.expander(f"{h['time']} | {h['id']}"):
            if st.button(f"↩ Restore {h['id']}"):
                st.session_state.current_intent = h["intent"]
                st.session_state.current_results = h["results"]
            st.json(h["results"])

    st.markdown('</div>', unsafe_allow_html=True)


def raw():
    st.json(st.session_state.current_results)


# -------------------- TABS --------------------
tabs = st.tabs([
    "▶ New Execution",
    "📝 Intent",
    "🧭 Timeline",
    "🛡 Policy",
    "📜 History",
    "📄 Raw"
])

with tabs[0]: start_execution()
with tabs[1]: intent_editor()
with tabs[2]: timeline()
with tabs[3]: policy()
with tabs[4]: history()
with tabs[5]: raw()
