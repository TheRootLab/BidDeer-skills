import re
import unicodedata
from typing import List

from core.checklist_model.models import ChecklistItem


CHINESE_DOMAIN_PHRASES = (
    "项目经理",
    "高级职称",
    "资质证书",
    "资格证书",
    "联合体",
    "偏离表",
    "高新技术企业证书",
    "有效期",
    "证书",
)


def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower()


def expand_query(item: ChecklistItem) -> List[str]:
    text = _normalize_text(f"{item.name} {item.requirement} {item.note}")
    text = (
        text.replace("三年", "3年")
        .replace("五年", "5年")
        .replace("一年", "1年")
    )

    keywords = set()

    number_unit_matches = re.findall(r"\d+(?:年|个月|万|元|项|个)", text)
    keywords.update(number_unit_matches)
    for match in number_unit_matches:
        if match.endswith("年"):
            number = match.removesuffix("年")
            if number.isdigit():
                keywords.add(f"{int(number) * 12}个月")

    for match in re.findall(r"[a-z0-9]+", text):
        if len(match) >= 2 and not match.isdigit():
            keywords.add(match)

    for trigger in ("复印件", "扫描件", "原件", "截图", "照片"):
        if trigger in text:
            keywords.add(trigger)

    for phrase in CHINESE_DOMAIN_PHRASES:
        normalized_phrase = _normalize_text(phrase)
        if normalized_phrase in text:
            keywords.add(normalized_phrase)

    for chunk in re.split(r"[，。、；（）\s]+", text):
        if len(chunk) > 1 and not chunk.isdigit():
            keywords.add(chunk)

    return list(keywords)
