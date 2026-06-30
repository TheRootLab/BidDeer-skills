"""Template for connecting proposal-point-checker to an external LLM.

This file is intentionally non-functional. It does not import or call any real
LLM SDK, does not read credentials, and does not make network requests.

Copy this template into your application code and replace the pseudo-code with
your own provider call.
"""

from __future__ import annotations

from typing import Any, Dict

from biddeer_checker.checklist_model.models import ChecklistItem
from biddeer_checker.evidence_reasoning.llm_adapter import LLMProviderAdapter
from biddeer_checker.evidence_reasoning.models import EvidenceStatus, ReasoningResult


class BridgeLLMProviderAdapter(LLMProviderAdapter):
    """Example adapter shape for host applications.

    The host application is responsible for credentials, provider SDKs, retry
    policy, JSON parsing, and provider-specific safety controls.
    """

    def __init__(self, client: Any, model_name: str):
        self.client = client
        self.model_name = model_name

    def invoke_reasoning(
        self,
        item: ChecklistItem,
        context_text: str,
    ) -> ReasoningResult:
        payload = self._build_payload(item, context_text)

        # Pseudo-code only:
        # raw_response = self.client.generate(model=self.model_name, input=payload)
        # data = parse_json(raw_response.text)
        data = self._call_external_provider(payload)

        return ReasoningResult(
            status=EvidenceStatus(data["status"]),
            reason=data["reason"],
            judgmentBasis=data["judgmentBasis"],
            manualCheckPrompt=data["manualCheckPrompt"],
        )

    def _build_payload(self, item: ChecklistItem, context_text: str) -> Dict[str, str]:
        return {
            "itemId": item.itemId,
            "name": item.name,
            "requirement": item.requirement,
            "note": item.note,
            "context": context_text,
            "outputContract": (
                "Return JSON with status, reason, judgmentBasis, "
                "and manualCheckPrompt. Status must be one of the six "
                "EvidenceStatus values."
            ),
        }

    def _call_external_provider(self, payload: Dict[str, str]) -> Dict[str, str]:
        raise NotImplementedError(
            "Replace this pseudo-code with your own LLM gateway call. "
            "Do not hard-code credentials in the Skill package."
        )
