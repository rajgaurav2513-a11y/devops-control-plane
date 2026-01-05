_execution_state = {}


def mark_stage_complete(execution_id: str, stage: str):
    _execution_state[execution_id] = stage


def get_last_completed_stage(execution_id: str):
    return _execution_state.get(execution_id)
