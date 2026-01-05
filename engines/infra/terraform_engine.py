# engines/infra/terraform_engine.py  (REPLACE FULL FILE)

import os
import json
import tempfile
import subprocess


def run_cmd(cmd, cwd, env=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def classify_terraform_error(stderr: str) -> dict:
    return {
        "severity": "MEDIUM",
        "category": "UNKNOWN_TERRAFORM_ERROR",
        "summary": "Terraform plan failed",
        "root_cause": stderr.strip(),
        "what_user_can_do": [
            "Check Terraform configuration",
            "Verify provider requirements",
        ],
        "what_system_prevented": [
            "Avoided unsafe infrastructure changes"
        ],
    }


def provision(intent: dict) -> dict:
    tf_dir = os.path.abspath(intent["infra"]["terraform_dir"])

    tf_env = {
        **os.environ,
        "AWS_ACCESS_KEY_ID": "dummy",
        "AWS_SECRET_ACCESS_KEY": "dummy",
        "AWS_SESSION_TOKEN": "dummy",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_EC2_METADATA_DISABLED": "true",
    }

    init = run_cmd(
        ["terraform", "init", "-input=false", "-no-color"],
        tf_dir,
        env=tf_env,
    )
    if init.returncode != 0:
        raise Exception(json.dumps(classify_terraform_error(init.stderr)))

    plan_file = tempfile.NamedTemporaryFile(delete=False).name

    plan = run_cmd(
        ["terraform", "plan", "-out", plan_file, "-input=false", "-no-color"],
        tf_dir,
        env=tf_env,
    )
    if plan.returncode != 0:
        os.unlink(plan_file)
        raise Exception(json.dumps(classify_terraform_error(plan.stderr)))

    show = run_cmd(
        ["terraform", "show", "-json", plan_file],
        tf_dir,
        env=tf_env,
    )
    os.unlink(plan_file)

    if show.returncode != 0:
        raise Exception("Failed to read terraform plan JSON")

    return json.loads(show.stdout)
