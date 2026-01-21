class PlatformContext:
    """
    Single source of truth for execution.
    No engine decides in isolation anymore.
    """

    def __init__(self, intent: dict):
        self.intent = intent
        self.env = intent.get("environment", "dev")

        self.workspace = None
        self.app_meta = {}
        self.image = None
        self.infra_profile = None
        self.deploy_target = None

    def set_workspace(self, path: str):
        self.workspace = path

    def set_app_meta(self, meta: dict):
        self.app_meta = meta

    def set_image(self, image: str):
        self.image = image

    def set_infra_profile(self, profile: str):
        self.infra_profile = profile

    def set_deploy_target(self, target: str):
        self.deploy_target = target
