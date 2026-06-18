import json
from typing import Any

from core.evidence_reasoning.llm_adapter import LLMProviderAdapter
from core.evidence_reasoning.models import (
    EvidenceStatus,
    JudgedEvidencePackage,
    ReasoningResult,
)
from core.evidence_reasoning.prompt_builder import assemble_context
from core.evidence_retrieval.models import EvidencePackage


def _invalid_output_result() -> ReasoningResult:
    return ReasoningResult(
        status=EvidenceStatus.UNABLE_TO_JUDGE,
        reason="LLM_OUTPUT_INVALID",
        judgmentBasis="",
        manualCheckPrompt="LLM 输出结构无效，请人工复核候选证据。",
    )


def _coerce_reasoning_result(raw_result: Any) -> ReasoningResult:
    if isinstance(raw_result, ReasoningResult):
        return raw_result
    if not isinstance(raw_result, dict):
        raise ValueError("LLM output must be ReasoningResult or dict.")

    required_fields = {"status", "reason", "judgmentBasis", "manualCheckPrompt"}
    if not required_fields.issubset(raw_result):
        raise ValueError("LLM output missing required fields.")

    try:
        status = EvidenceStatus(raw_result["status"])
    except ValueError as error:
        raise ValueError("LLM output status is invalid.") from error

    return ReasoningResult(
        status=status,
        reason=raw_result["reason"],
        judgmentBasis=raw_result["judgmentBasis"],
        manualCheckPrompt=raw_result["manualCheckPrompt"],
    )


class ReasoningEngine:
    def __init__(
        self,
        adapter: LLMProviderAdapter,
        max_attempts: int = 2,
        soft_char_limit: int = 12000,
    ):
        self.adapter = adapter
        self.max_attempts = min(max(max_attempts, 1), 3)
        self.soft_char_limit = soft_char_limit

    def judge(self, package: EvidencePackage) -> JudgedEvidencePackage:
        if not package.candidates:
            return JudgedEvidencePackage(
                package=package,
                result=ReasoningResult(
                    status=EvidenceStatus.NOT_FOUND,
                    reason="NO_CANDIDATE_EVIDENCE",
                    judgmentBasis="",
                    manualCheckPrompt="未找到候选证据，请人工检查原文是否遗漏相关材料。",
                ),
            )

        context_text = assemble_context(
            package.candidates,
            soft_char_limit=self.soft_char_limit,
        )
        last_error = None
        for _attempt in range(self.max_attempts):
            try:
                result = _coerce_reasoning_result(
                    self.adapter.invoke_reasoning(package.item, context_text)
                )
                return JudgedEvidencePackage(
                    package=package,
                    result=result,
                )
            except (json.JSONDecodeError, ValueError):
                try:
                    result = _coerce_reasoning_result(
                        self.adapter.invoke_reasoning(package.item, context_text)
                    )
                    return JudgedEvidencePackage(
                        package=package,
                        result=result,
                    )
                except (json.JSONDecodeError, ValueError):
                    return JudgedEvidencePackage(
                        package=package,
                        result=_invalid_output_result(),
                    )
                except Exception as error:
                    last_error = error
                    break
            except Exception as error:
                last_error = error

        return JudgedEvidencePackage(
            package=package,
            result=ReasoningResult(
                status=EvidenceStatus.UNABLE_TO_JUDGE,
                reason="LLM_API_ERROR",
                judgmentBasis="",
                manualCheckPrompt=(
                    "LLM API 调用失败，请人工复核候选证据。"
                    f" 错误类型：{type(last_error).__name__ if last_error else 'UNKNOWN'}"
                ),
            ),
        )
