# core/orchestrator/executor.py
# FINAL SYNCED EXECUTOR – SOURCE FIXED, NO ARCH CHANGE

import os
import sys
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.models.result import ExecutionResult, Status
from core.intent.validator import validate_intent
from core.policy.evaluator import evaluate_policies
from core.observability.rules import evaluate_health, ALLOW
from core.observability.error_normalizer import normalize_error

from state.execution_store import mark_stage_complete, get_last_completed_stage
from state.snapshots import save_snapshot

# INFRA
from engines.infra.terraform.terraform_engine import provision

# SOURCE / BUILD / DEPLOY
from engines.source.git_agent import prepare_source, cleanup_source
from engines.container.builder import build_image
from engines.container.docker_runner import run_container
from engines.container.docker_health import docker_available
from engines.container.adapters.image_publish import publish_image
from engines.config.rolling import rolling_apply

# TEST & QUALITY
from engines.testing.runner import run_tests
from engines.quality.runner import run_quality_checks


STAGE_ORDER = [
    "INFRA",
    "CONFIG",
    "SOURCE",
    "BUILD",
    "IMAGE-PUBLISH",
    "RUN",
    "TEST",
    "QUALITY",
    "HEALTH",
    "POLICY",
    "CONFIG-ROLLING",
    "SNAPSHOT",
]


def execute(intent: dict):
    results = []

    execution_id = str(uuid.uuid4())[:8]
    intent["_execution"] = {"id": execution_id}

    meta = intent.get("_meta", {})
    trigger = meta.get("trigger", "ui")
    intent_id = meta.get("intent_id", execution_id)

    print(f"[EXECUTOR] intent_id={intent_id} trigger={trigger}")

    last_completed = get_last_completed_stage(execution_id)

    def should_run(stage: str):
        if not last_completed:
            return True
        return STAGE_ORDER.index(stage) > STAGE_ORDER.index(last_completed)

    app = intent.get("application", {})
    code_present = bool(app)

    build_enabled = (
        "image" in intent
        and isinstance(intent.get("image"), dict)
        and bool(intent["image"].get("name"))
    )

    publish_enabled = build_enabled and isinstance(intent["image"].get("publish"), dict)

    run_enabled = (
        build_enabled and intent.get("deploy", {}).get("mode") == "local-docker"
    )

    # ===== INFRA =====
    if "infrastructure" in intent and should_run("INFRA"):
        try:
            provision(intent)
            r = ExecutionResult("INFRA", Status.SUCCESS, "Terraform evaluated")
        except Exception as e:
            r = normalize_error("INFRA", e)

        results.append(r)
        if r.status == Status.BLOCKED:
            return results
        mark_stage_complete(execution_id, "INFRA")

    # ===== CONFIG =====
    if should_run("CONFIG"):
        try:
            r = validate_intent(intent)
        except Exception as e:
            r = normalize_error("CONFIG", e)

        results.append(r)
        if r.status != Status.SUCCESS:
            return results
        mark_stage_complete(execution_id, "CONFIG")

    # ===== SOURCE (FIXED) =====
    if code_present and should_run("SOURCE"):
        try:
            app = intent["application"]

            # Local shortcut only if path explicitly provided
            if "path" in app and app.get("path"):
                workspace = os.path.abspath(app["path"])
            else:
                workspace = prepare_source(intent)

            if not workspace or not os.path.isdir(workspace):
                return [
                    ExecutionResult(
                        "SOURCE",
                        Status.BLOCKED,
                        "Workspace could not be prepared",
                    )
                ]

            intent["_execution"]["workspace"] = workspace
            mark_stage_complete(execution_id, "SOURCE")

        except Exception as e:
            return [normalize_error("SOURCE", e)]

    # ===== BUILD =====
    if build_enabled and should_run("BUILD"):
        if not docker_available():
            return [ExecutionResult("BUILD", Status.BLOCKED, "Docker not reachable")]

        try:
            r = build_image(intent)
        except Exception as e:
            r = normalize_error("BUILD", e)

        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "BUILD")
    else:
        mark_stage_complete(execution_id, "BUILD")

    # ===== IMAGE PUBLISH =====
    if publish_enabled and should_run("IMAGE-PUBLISH"):
        try:
            r = publish_image(intent)
        except Exception as e:
            r = normalize_error("IMAGE-PUBLISH", e)

        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "IMAGE-PUBLISH")

    # ===== RUN =====
    if run_enabled and should_run("RUN"):
        image = f"{intent['application']['name']}:{execution_id}"
        try:
            r = run_container(intent, image)
        except Exception as e:
            r = normalize_error("RUN", e)

        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "RUN")

    # ===== TEST =====
    if should_run("TEST"):
        try:
            r = run_tests(intent)
        except Exception as e:
            r = normalize_error("TEST", e)

        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "TEST")

    # ===== QUALITY =====
    if should_run("QUALITY"):
        try:
            r = run_quality_checks(intent)
        except Exception as e:
            r = normalize_error("QUALITY", e)

        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "QUALITY")

    # ===== HEALTH =====
    if should_run("HEALTH"):
        try:
            h = evaluate_health(intent.get("environment", "dev"))
            status = Status.SUCCESS if h["decision"] == ALLOW else Status.BLOCKED
            r = ExecutionResult("HEALTH", status, h["reason"])
        except Exception as e:
            r = normalize_error("HEALTH", e)

        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "HEALTH")

    # ===== POLICY =====
    if should_run("POLICY"):
        try:
            pr = evaluate_policies(intent)
        except Exception as e:
            pr = [normalize_error("POLICY", e)]

        results.extend(pr)
        if any(x.status == Status.BLOCKED for x in pr):
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "POLICY")

    # ===== CONFIG ROLLING =====
    if "config" in intent and should_run("CONFIG-ROLLING"):
        try:
            r = rolling_apply(intent)
        except Exception as e:
            r = normalize_error("CONFIG-ROLLING", e)

        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "CONFIG-ROLLING")

    # ===== SNAPSHOT =====
    if should_run("SNAPSHOT"):
        try:
            save_snapshot(intent)
            r = ExecutionResult("SNAPSHOT", Status.SUCCESS, "Snapshot saved")
        except Exception as e:
            r = normalize_error("SNAPSHOT", e)

        results.append(r)
        mark_stage_complete(execution_id, "SNAPSHOT")

    cleanup_source(intent)
    return results
