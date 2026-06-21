from typing import List

from biddeer_checker.evidence_retrieval.models import CandidateEvidence


def _trim_to_limit(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit <= 3:
        return "." * limit
    return text[: limit - 3] + "..."


def _candidate_section(candidate: CandidateEvidence, index: int, context_limit: int) -> str:
    locator = candidate.userLocator
    heading_path = " > ".join(locator.headingPath)
    fixed_parts = [
        f"候选证据 {index}",
        f"命中文本: {candidate.exactText}",
        f"matchedKeywords: {', '.join(candidate.matchedKeywords)}",
        f"sourceDocName: {locator.sourceDocName}",
        f"headingPath: {heading_path}",
        f"nearestHeading: {locator.nearestHeading or ''}",
        f"locatorHint: {locator.locatorHint}",
        f"evidenceType: {locator.evidenceType}",
        f"blockIndex: {candidate.blockIndex}",
        f"rowIndex: {candidate.rowIndex}",
    ]
    for image in candidate.nearbyImages:
        fixed_parts.append(f"[注：此处附有图片，ID：{image.imageId}]")

    fixed_text = "\n".join(fixed_parts)
    if context_limit <= len(fixed_text):
        return fixed_text

    remaining = context_limit - len(fixed_text)
    pre_budget = remaining // 2
    post_budget = remaining - pre_budget
    context_parts = []
    if candidate.preContext:
        context_parts.append(f"前文: {_trim_to_limit(candidate.preContext, pre_budget)}")
    if candidate.postContext:
        context_parts.append(f"后文: {_trim_to_limit(candidate.postContext, post_budget)}")

    if context_parts:
        return "\n".join([fixed_text, *context_parts])
    return fixed_text


def assemble_context(
    candidates: List[CandidateEvidence],
    soft_char_limit: int = 12000,
) -> str:
    if not candidates:
        return ""

    separator = "\n\n"
    separator_budget = len(separator) * (len(candidates) - 1)
    per_candidate_limit = max(
        1,
        (soft_char_limit - separator_budget) // len(candidates),
    )
    sections = []
    for index, candidate in enumerate(candidates, start=1):
        sections.append(_candidate_section(candidate, index, per_candidate_limit))

    context = separator.join(sections)
    if len(context) > soft_char_limit:
        return _trim_to_limit(context, soft_char_limit)
    return context
