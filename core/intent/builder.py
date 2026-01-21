"""
Shared Intent Builder
Used by:
- UI (manual intent)
- Future webhooks
- Future CLI

This file does NOT execute anything.
"""

from typing import Dict, Any
import uuid
import datetime


def base_intent(environment: str, execution_mode: str) -> Dict[str, Any]:
    return {
        "_meta": {
            "intent_id": str(uuid.uuid4())[:8],
            "created_at": datetime.datetime.utcnow().isoformat(),
            "trigger": "ui"   # ui | webhook | cli (future)
        },
        "environment": environment,
        "execution": {
            "mode": execution_mode
        }
    }


def with_source(intent: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    intent["source"] = source
    return intent


def with_infrastructure(intent: Dict[str, Any], infra: Dict[str, Any]) -> Dict[str, Any]:
    intent["infrastructure"] = infra
    return intent


def with_config(intent: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    intent["config"] = config
    return intent


def with_kubernetes(intent: Dict[str, Any], k8s: Dict[str, Any]) -> Dict[str, Any]:
    intent["kubernetes"] = k8s
    return intent


def with_pipeline(intent: Dict[str, Any], pipeline: Dict[str, Any]) -> Dict[str, Any]:
    intent["pipeline"] = pipeline
    return intent
