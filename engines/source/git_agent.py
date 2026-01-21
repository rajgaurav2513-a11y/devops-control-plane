import os
import shutil
import tempfile
import time
import stat
import urllib.request
import zipfile
import io


def _on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _download_github_zip(repo: str, branch: str):
    # IMPORTANT: never use rstrip(".git")
    base = repo[:-4] if repo.endswith(".git") else repo

    candidates = [
        f"{base}/archive/refs/heads/{branch}.zip",
        f"{base}/archive/{branch}.zip",
        f"{base}/archive/refs/heads/main.zip",
        f"{base}/archive/main.zip",
        f"{base}/archive/refs/heads/master.zip",
        f"{base}/archive/master.zip",
    ]

    errors = []

    for url in candidates:
        try:
            with urllib.request.urlopen(url) as resp:
                return resp.read(), url
        except Exception as e:
            errors.append(f"{url} -> {e}")

    raise RuntimeError(
        "Failed to download GitHub repository ZIP.\n"
        "Tried the following URLs:\n" +
        "\n".join(errors)
    )


def prepare_source(intent: dict) -> str:
    app = intent.get("application")
    if not app:
        raise RuntimeError("Missing 'application' block in intent")

    # ---- intent normalization ----
    if "source" not in app:
        app["source"] = {
            "type": "git",
            "repo": app.get("repo"),
            "branch": app.get("branch", "main"),
        }

    source = app.get("source", {})
    source_type = source.get("type", "git")
    exec_id = intent["_execution"]["id"]

    # ---- local source ----
    if source_type == "local":
        path = source.get("path")
        if not path:
            raise RuntimeError("Local source path missing")

        abs_path = os.path.abspath(path)
        if not os.path.isdir(abs_path):
            raise RuntimeError(f"Local source path not found: {abs_path}")

        return abs_path

    # ---- remote github zip ----
    repo = source.get("repo")
    if not repo:
        raise RuntimeError("Git source selected but repo not provided")

    branch = source.get("branch", "main")

    if "github.com" not in repo:
        raise RuntimeError("Only public GitHub repos supported (ZIP mode)")

    base_tmp = tempfile.gettempdir()
    workspace = os.path.join(base_tmp, "devops-control-plane", exec_id)

    if os.path.exists(workspace):
        shutil.rmtree(workspace, onerror=_on_rm_error)

    os.makedirs(workspace, exist_ok=True)

    zip_data, _ = _download_github_zip(repo, branch)

    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        z.extractall(workspace)

    extracted = os.listdir(workspace)
    if not extracted:
        raise RuntimeError("ZIP extracted but no files found")

    extracted_root = os.path.join(workspace, extracted[0])

    for item in os.listdir(extracted_root):
        shutil.move(
            os.path.join(extracted_root, item),
            os.path.join(workspace, item),
        )

    shutil.rmtree(extracted_root)

    return workspace


def cleanup_source(intent: dict):
    app = intent.get("application", {})
    source = app.get("source", {})

    if source.get("type") == "local":
        return

    exec_id = intent["_execution"]["id"]
    workspace = os.path.join(
        tempfile.gettempdir(),
        "devops-control-plane",
        exec_id
    )

    if not os.path.exists(workspace):
        return

    for _ in range(5):
        try:
            shutil.rmtree(workspace, onerror=_on_rm_error)
            return
        except PermissionError:
            time.sleep(1)
