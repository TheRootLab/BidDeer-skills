#!/usr/bin/env python3
"""Generate synthetic demo images for the enhanced proposal PDF.

Creates:
  - bli.png: synthetic business license image (营业执照)
  - PM.png: synthetic project management training certificate (项目管理培训证书)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = (
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
)


def resolve_font_path() -> Path:
    for candidate in FONT_CANDIDATES:
        p = Path(candidate)
        if p.is_file():
            return p
    raise FileNotFoundError("No CJK font found")


def make_business_license(font_path: Path, output_path: Path) -> None:
    """Synthetic business license image with visible registered capital field."""
    img = Image.new("RGB", (1600, 1100), "white")
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.truetype(str(font_path), size=48)
    body_font = ImageFont.truetype(str(font_path), size=36)
    small_font = ImageFont.truetype(str(font_path), size=28)

    draw.rectangle((35, 35, 1565, 1065), outline="#1a1a2e", width=4)
    draw.rectangle((45, 45, 1555, 1055), outline="#1a1a2e", width=2)

    center_x = 800

    def centered_text(draw, y, text, font, fill="#1a1a2e"):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((center_x - tw // 2), y), text, font=font, fill=fill)

    centered_text(draw, 90, "营业执照", title_font, fill="#c8102e")

    title2 = ImageFont.truetype(str(font_path), size=22)
    centered_text(draw, 155, "（合成演示用 · 非真实执照）", title2, fill="#999999")

    fields = [
        ("统一社会信用代码", "91110000MA0000000X"),
        ("名称", "神鹿测试科技有限公司"),
        ("类型", "有限责任公司（自然人投资或控股）"),
        ("法定代表人", "合成示例人员 C"),
        ("注册资本", "人民币壹佰万元"),
        ("成立日期", "2020年01月15日"),
        ("营业期限", "2020年01月15日 至 长期"),
        ("住所", "北京市海淀区中关村合成路100号"),
        ("登记机关", "北京市合成市场监督管理局"),
        ("登记日期", "2025年12月01日"),
    ]

    y = 230
    for label, value in fields:
        draw.text((160, y), label, font=body_font, fill="#333333")
        draw.text((560, y), value, font=body_font, fill="#1a1a2e")
        draw.line((160, y + 48, 1400, y + 48), fill="#dddddd", width=1)
        y += 58

    draw.text((160, y + 30), "备注：本图片为合成演示用图像，不具备法律效力。", font=small_font, fill="#999999")

    draw.text(
        (160, y + 90),
        "注册资本字段可见值为“人民币壹佰万元”，即人民币 100 万元。",
        font=small_font,
        fill="#666666",
    )

    img.save(output_path, format="PNG")
    print(f"Created: {output_path}")


def make_training_certificate(font_path: Path, output_path: Path) -> None:
    """Synthetic project management training certificate with visible date."""
    img = Image.new("RGB", (1600, 1100), "#faf8f3")
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.truetype(str(font_path), size=56)
    body_font = ImageFont.truetype(str(font_path), size=36)
    small_font = ImageFont.truetype(str(font_path), size=28)

    draw.rectangle((40, 40, 1560, 1060), outline="#1a3c6d", width=6)
    draw.rectangle((55, 55, 1545, 1045), outline="#1a3c6d", width=2)

    center_x = 800

    def centered_text(draw, y, text, font, fill="#1a3c6d"):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((center_x - tw // 2), y), text, font=font, fill=fill)

    centered_text(draw, 100, "项目管理培训证书", title_font)

    subtitle = ImageFont.truetype(str(font_path), size=22)
    centered_text(draw, 170, "（合成演示用 · 非真实证书）", subtitle, fill="#999999")

    cert_fields = [
        ("证书编号", "BD-PM-TRAIN-2026-001"),
        ("持证人", "张三"),
        ("培训课程", "项目管理基础与实践"),
        ("培训日期", "2026-07-08"),
        ("培训机构", "合成项目管理办法测试中心"),
        ("证书状态", "已完成"),
    ]

    y = 280
    for label, value in cert_fields:
        draw.text((280, y), label, font=body_font, fill="#555555")
        draw.text((530, y), value, font=body_font, fill="#1a3c6d")
        draw.line((280, y + 52, 1320, y + 52), fill="#cccccc", width=1)
        y += 68

    y += 40
    centered_text(draw, y, "兹证明持证人已完成上述培训内容。", body_font, fill="#1a3c6d")

    y += 80
    draw.text((280, y), "签发日期：2026-07-08", font=body_font, fill="#1a3c6d")
    draw.text((1050, y), "签发机构（合成用章）", font=body_font, fill="#555555")

    draw.ellipse((1020, y + 50, 1380, y + 350), outline="#c83232", width=8)
    draw.text(
        (1075, y + 155), "合成演示", font=ImageFont.truetype(str(font_path), size=28), fill="#c83232"
    )

    y += 400
    draw.text(
        (160, y),
        "备注：本图片为合成演示用图像，培训日期为 2026-07-08，不满足“距审核日期超过 1 年”的演示条件。",
        font=small_font,
        fill="#999999",
    )

    img.save(output_path, format="PNG")
    print(f"Created: {output_path}")


def main() -> None:
    font_path = resolve_font_path()
    print(f"Using font: {font_path}")

    pictures_dir = Path(__file__).parent / "pictures"
    pictures_dir.mkdir(parents=True, exist_ok=True)

    make_business_license(font_path, pictures_dir / "bli.png")
    make_training_certificate(font_path, pictures_dir / "PM.png")


if __name__ == "__main__":
    main()
