import os
import shutil
import subprocess
import tempfile
import time
import stat


def _on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def prepare_source(intent: dict) -> str:
    source = intent.get("source", {"type": "local"})
    exec_id = intent["_execution"]["id"]

    # -------------------------
    # LOCAL SOURCE
    # -------------------------
    if source.get("type") == "local":
        return intent.get("application", {}).get("path")

    # -------------------------
    # GIT SOURCE
    # -------------------------
    repo = source["repo"]
    branch = source.get("branch", "main")
    commit = source.get("commit")
    auth = source.get("auth")

    base_tmp = tempfile.gettempdir()
    workspace = os.path.join(base_tmp, "devops-control-plane", exec_id)

    if os.path.exists(workspace):
        shutil.rmtree(workspace, onerror=_on_rm_error)

    os.makedirs(workspace, exist_ok=True)

    clone_cmd = ["git", "clone", "--depth", "1", "-b", branch]

    # 🔐 PRIVATE REPO AUTH (TOKEN)
    if auth and auth.get("type") == "token":
        token_env = auth.get("token_env")
        token = os.getenv(token_env)

        if not token:
            raise RuntimeError(f"Git token env var not set: {token_env}")

        # Insert token safely into URL (never logged)
        repo = repo.replace(
            "https://",
            f"https://{token}@"
        )

    clone_cmd.extend([repo, workspace])

    subprocess.check_call(clone_cmd)

    if commit:
        subprocess.check_call(
            ["git", "checkout", commit],
            cwd=workspace
        )

    return workspace


def cleanup_source(intent: dict):
    source = intent.get("source", {"type": "local"})

    if source.get("type") != "git":
        return

    exec_id = intent["_execution"]["id"]
    base_tmp = tempfile.gettempdir()
    workspace = os.path.join(base_tmp, "devops-control-plane", exec_id)

    if not os.path.exists(workspace):
        return

    for _ in range(5):
        try:
            shutil.rmtree(workspace, onerror=_on_rm_error)
            return
        except PermissionError:
            time.sleep(1)

    print(f"[WARN] Could not fully delete workspace: {workspace}")
