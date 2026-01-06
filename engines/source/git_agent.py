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


def prepare_source(intent: dict) -> str | None:
    # ✅ SINGLE SOURCE OF TRUTH
    app = intent.get("application")
    if not app:
        return None

    source = app.get("source", {})
    source_type = source.get("type", "local")
    exec_id = intent["_execution"]["id"]

    # -------------------------
    # LOCAL SOURCE (FINAL FIX)
    # -------------------------
    if source_type == "local":
        path = source.get("path")
        if not path:
            return None

        abs_path = os.path.abspath(path)

        if not os.path.isdir(abs_path):
            return None

        return abs_path

    # -------------------------
    # GIT SOURCE (UNCHANGED)
    # -------------------------
    repo = source.get("repo")
    if not repo:
        return None

    branch = source.get("branch", "main")
    commit = source.get("commit")
    auth = source.get("auth")

    base_tmp = tempfile.gettempdir()
    workspace = os.path.join(base_tmp, "devops-control-plane", exec_id)

    if os.path.exists(workspace):
        shutil.rmtree(workspace, onerror=_on_rm_error)

    os.makedirs(workspace, exist_ok=True)

    clone_cmd = ["git", "clone", "--depth", "1", "-b", branch]

    if auth and auth.get("type") == "token":
        token_env = auth.get("token_env")
        token = os.getenv(token_env)
        if not token:
            raise RuntimeError(f"Git token env var not set: {token_env}")
        repo = repo.replace("https://", f"https://{token}@")

    clone_cmd.extend([repo, workspace])
    subprocess.check_call(clone_cmd)

    if commit:
        subprocess.check_call(["git", "checkout", commit], cwd=workspace)

    return workspace


def cleanup_source(intent: dict):
    app = intent.get("application", {})
    source = app.get("source", {})

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
