def requires_approval(decision_snapshot) -> bool:
    return (
        decision_snapshot.final_status == "ALLOW"
        and decision_snapshot.risk_level in ("MEDIUM", "HIGH")
    )
