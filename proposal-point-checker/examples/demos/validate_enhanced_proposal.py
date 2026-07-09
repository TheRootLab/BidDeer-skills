#!/usr/bin/env python3
"""Validate the enhanced proposal PDF meets quality requirements.

Checks:
  - Exactly 8 pages
  - Pages 1-6 have sufficient Chinese text density
  - Pages 7-8 have embedded images
  - No old English section skeleton
  - All required Chinese section titles present
"""

from pathlib import Path
import sys
import fitz


PDF_PATH = Path(__file__).parent / "picture-review-enhanced" / "inputs" / "enhanced_proposal.pdf"


def validate() -> int:
    if not PDF_PATH.is_file():
        print(f"ERROR: PDF not found at {PDF_PATH}")
        return 1

    doc = fitz.open(PDF_PATH)
    errors = []

    if len(doc) != 8:
        errors.append(f"Expected 8 pages, got {len(doc)}")

    min_chars_by_page = {
        1: 350, 2: 350, 3: 350, 4: 300, 5: 300, 6: 300, 7: 120, 8: 120,
    }

    total_images = 0
    for page_index, page in enumerate(doc, start=1):
        text = page.get_text()
        images = page.get_images(full=True)
        total_images += len(images)
        compact_text = "".join(text.split())

        char_count = len(compact_text)
        if char_count < min_chars_by_page[page_index]:
            errors.append(
                f"Page {page_index} too sparse: {char_count} chars "
                f"(min: {min_chars_by_page[page_index]})"
            )

        if page_index == 7 and len(images) < 1:
            errors.append("Page 7 missing business license image")
        if page_index == 8 and len(images) < 1:
            errors.append("Page 8 missing training certificate image")

    if total_images < 2:
        errors.append(f"Expected >= 2 embedded images, got {total_images}")

    full_text = "\n".join(page.get_text() for page in doc)

    required_chinese = [
        "第 1 节：项目概述",
        "第 2 节：项目管理",
        "第 3 节：服务能力与资质",
        "第 4 节：保密承诺",
        "第 5 节：培训计划",
        "第 6 节：交付计划",
        "附件 A：营业执照图片",
        "附件 B：项目管理培训证书图片",
    ]
    for text in required_chinese:
        if text not in full_text:
            errors.append(f"Missing Chinese heading: {text}")

    old_english_phrases = [
        "Section 1: Executive Summary",
        "Section 2: Project Management",
        "Section 3: Service Capability and Qualifications",
        "Section 4: Confidentiality Commitment",
        "Section 5: Training Plan",
        "Section 6: Delivery Plan",
        "Appendix A: Business License Image",
        "Appendix B: Project Management Training Certificate Image",
        "Synthetic Proposal - Public Demo Only - No Real Data",
    ]
    for phrase in old_english_phrases:
        if phrase in full_text:
            errors.append(f"Old English text remains: {phrase}")

    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"VALIDATION OK: {len(doc)} pages, {total_images} images, all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
