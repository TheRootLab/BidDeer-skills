from abc import ABC, abstractmethod

from core.checklist_model.models import ChecklistItem
from core.evidence_reasoning.models import ReasoningResult


class LLMProviderAdapter(ABC):
    @abstractmethod
    def invoke_reasoning(
        self,
        item: ChecklistItem,
        context_text: str,
    ) -> ReasoningResult:
        raise NotImplementedError
