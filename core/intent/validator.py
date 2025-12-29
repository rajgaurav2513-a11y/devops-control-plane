
import yaml
def validate_intent(path):
    with open(path) as f:
        return yaml.safe_load(f)
