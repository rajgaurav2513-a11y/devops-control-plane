
from core.intent.validator import validate_intent
from core.policy.engine import apply_policies
from core.orchestrator.executor import execute

if __name__ == "__main__":
    intent = validate_intent("examples/intent-prod.yaml")
    intent = apply_policies(intent)
    execute(intent)
