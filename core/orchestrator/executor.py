
from engines.infra.terraform_engine import provision
from engines.container.builder import build_image
from engines.deploy.k8s_engine import deploy_app
from state.snapshots import save_snapshot

def execute(intent):
    print("Starting execution flow")
    infra_state = provision(intent)
    image = build_image(intent)
    deploy_app(intent, image)
    save_snapshot(intent)
    print("Execution completed safely")
