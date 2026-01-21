# engines/infra/terraform/terraform_engine.py
# (FULL CORRECTED FILE – DROP-IN REPLACEMENT)

import os
import json
import tempfile
import subprocess
from typing import Dict


def run_cmd(cmd, cwd, env=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def classify_terraform_error(stderr: str) -> Dict:
    return {
        "severity": "MEDIUM",
        "category": "TERRAFORM_PLAN_ERROR",
        "summary": "Terraform plan failed",
        "root_cause": stderr.strip(),
        "what_user_can_do": [
            "Check Terraform configuration",
            "Verify provider credentials",
            "Validate variables and backend",
        ],
        "what_system_prevented": [
            "Blocked unsafe infrastructure execution"
        ],
    }


def provision(intent: dict) -> Dict:
    """
    Executes Terraform INIT + PLAN + SHOW(JSON)
    PLAN ONLY – NO APPLY
    """

    # ===== CORRECT INTENT KEY =====
    infra_cfg = intent.get("infrastructure", {})

    # ===== TERRAFORM DIRECTORY =====
    tf_dir = infra_cfg.get("terraform_dir")

    if not tf_dir:
        raise Exception(
            json.dumps({
                "category": "INVALID_INTENT",
                "summary": "terraform_dir not provided",
                "root_cause": "Missing infrastructure.terraform_dir in intent",
                "what_user_can_do": [
                    "Provide terraform_dir in infrastructure block"
                ],
            })
        )

    tf_dir = os.path.abspath(tf_dir)

    if not os.path.isdir(tf_dir):
        raise Exception(
            json.dumps({
                "category": "INVALID_TERRAFORM_DIR",
                "summary": "Terraform directory not found",
                "root_cause": tf_dir,
                "what_user_can_do": [
                    "Verify terraform_dir path",
                    "Ensure main.tf exists"
                ],
            })
        )

    # ===== SAFE ENV (NO METADATA, NO REAL CREDS) =====
    tf_env = {
        **os.environ,
        "AWS_ACCESS_KEY_ID": infra_cfg.get("aws_access_key_id", "dummy"),
        "AWS_SECRET_ACCESS_KEY": infra_cfg.get("aws_secret_access_key", "dummy"),
        "AWS_SESSION_TOKEN": infra_cfg.get("aws_session_token", "dummy"),
        "AWS_DEFAULT_REGION": infra_cfg.get("region", "us-east-1"),
        "AWS_EC2_METADATA_DISABLED": "true",
    }

    # ===== TERRAFORM INIT =====
    init = run_cmd(
        ["terraform", "init", "-input=false", "-no-color"],
        tf_dir,
        env=tf_env,
    )

    if init.returncode != 0:
        raise Exception(json.dumps(classify_terraform_error(init.stderr)))

    # ===== TERRAFORM PLAN =====
    plan_file = tempfile.NamedTemporaryFile(delete=False).name

    plan = run_cmd(
        ["terraform", "plan", "-out", plan_file, "-input=false", "-no-color"],
        tf_dir,
        env=tf_env,
    )

    if plan.returncode != 0:
        os.unlink(plan_file)
        raise Exception(json.dumps(classify_terraform_error(plan.stderr)))

    # ===== TERRAFORM SHOW (JSON) =====
    show = run_cmd(
        ["terraform", "show", "-json", plan_file],
        tf_dir,
        env=tf_env,
    )

    os.unlink(plan_file)

    if show.returncode != 0:
        raise Exception(
            json.dumps({
                "category": "PLAN_READ_ERROR",
                "summary": "Failed to read terraform plan JSON",
                "root_cause": show.stderr.strip(),
                "what_user_can_do": [
                    "Re-run terraform plan manually"
                ],
            })
        )

    return json.loads(show.stdout)
