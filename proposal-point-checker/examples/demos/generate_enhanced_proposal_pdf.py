#!/usr/bin/env python3
"""Generate the 8-page enhanced Chinese proposal demo PDF.

Uses reportlab with embedded CJK TTF font for proper Chinese rendering.
Pages 7-8 embed the synthetic business license and training certificate images.
"""

from pathlib import Path
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    ListFlowable,
    ListItem,
    KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth

FONT_CANDIDATES = (
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
)

DEMO_DIR = Path(__file__).parent
PICTURES_DIR = DEMO_DIR / "pictures"
OUTPUT_DIR = DEMO_DIR / "picture-review-enhanced" / "inputs"
FONT_NAME = "BidDeerCJK"
FONT_NAME_BOLD = "BidDeerCJKBold"

PAGE_W, PAGE_H = A4

DARK = HexColor("#1a1a2e")
ACCENT = HexColor("#c8102e")
MID_GREY = HexColor("#666666")
LIGHT_GREY = HexColor("#eeeeee")
TABLE_HEADER_BG = HexColor("#2c3e50")
TABLE_ROW_ALT = HexColor("#f8f9fa")
BORDER_COLOR = HexColor("#dee2e6")
FOOTER_COLOR = HexColor("#999999")
PROPOSAL_BLUE = HexColor("#1a3c6d")


def resolve_font_path() -> Path:
    for candidate in FONT_CANDIDATES:
        p = Path(candidate)
        if p.is_file():
            return p
    raise FileNotFoundError("No CJK font found")


def register_fonts(font_path: Path) -> None:
    pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))
    pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, str(font_path)))


def build_styles() -> dict:
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            fontName=FONT_NAME,
            fontSize=22,
            leading=32,
            textColor=DARK,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle",
            fontName=FONT_NAME,
            fontSize=16,
            leading=24,
            textColor=DARK,
            spaceBefore=18,
            spaceAfter=8,
        ),
        "subsection_title": ParagraphStyle(
            "SubsectionTitle",
            fontName=FONT_NAME,
            fontSize=13,
            leading=20,
            textColor=DARK,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=17,
            textColor=HexColor("#333333"),
            alignment=TA_JUSTIFY,
            spaceBefore=2,
            spaceAfter=4,
            firstLineIndent=21,
        ),
        "body_no_indent": ParagraphStyle(
            "BodyNoIndent",
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=17,
            textColor=HexColor("#333333"),
            alignment=TA_JUSTIFY,
            spaceBefore=2,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=17,
            textColor=HexColor("#333333"),
            leftIndent=20,
            bulletIndent=8,
            spaceBefore=1,
            spaceAfter=1,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontName=FONT_NAME,
            fontSize=9.5,
            leading=14,
            textColor=white,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            fontName=FONT_NAME,
            fontSize=9,
            leading=13,
            textColor=HexColor("#333333"),
        ),
        "table_cell_center": ParagraphStyle(
            "TableCellCenter",
            fontName=FONT_NAME,
            fontSize=9,
            leading=13,
            textColor=HexColor("#333333"),
            alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "Footer",
            fontName=FONT_NAME,
            fontSize=7.5,
            leading=10,
            textColor=FOOTER_COLOR,
            alignment=TA_CENTER,
        ),
        "page_number": ParagraphStyle(
            "PageNumber",
            fontName=FONT_NAME,
            fontSize=8,
            leading=10,
            textColor=FOOTER_COLOR,
            alignment=TA_CENTER,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName=FONT_NAME,
            fontSize=11,
            leading=16,
            textColor=MID_GREY,
            alignment=TA_CENTER,
        ),
        "appendix_title": ParagraphStyle(
            "AppendixTitle",
            fontName=FONT_NAME,
            fontSize=18,
            leading=28,
            textColor=DARK,
            spaceBefore=10,
            spaceAfter=12,
        ),
        "appendix_body": ParagraphStyle(
            "AppendixBody",
            fontName=FONT_NAME,
            fontSize=10,
            leading=16,
            textColor=HexColor("#333333"),
            spaceBefore=2,
            spaceAfter=4,
        ),
        "boundary_note": ParagraphStyle(
            "BoundaryNote",
            fontName=FONT_NAME,
            fontSize=9,
            leading=14,
            textColor=HexColor("#888888"),
            alignment=TA_LEFT,
        ),
    }
    return styles


def hr():
    return HRFlowable(
        width="100%",
        thickness=0.5,
        color=BORDER_COLOR,
        spaceBefore=4,
        spaceAfter=4,
    )


def make_table(headers, rows, col_widths=None, styles=None):
    s = styles or {}
    hdr_cells = [Paragraph(h, s.get("table_header", build_styles()["table_header"])) for h in headers]
    data = [hdr_cells]
    cell_style = s.get("table_cell", build_styles()["table_cell"])
    center_style = s.get("table_cell_center", build_styles()["table_cell_center"])
    for row in rows:
        data.append([Paragraph(str(c), cell_style) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    base_style = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            base_style.append(("BACKGROUND", (0, i), (-1, i), TABLE_ROW_ALT))
    t.setStyle(TableStyle(base_style))
    return t


def bullet(text, styles=None):
    s = styles or build_styles()
    return Paragraph(f"\u2022  {text}", s["bullet"])


def body(text, styles=None):
    s = styles or build_styles()
    return Paragraph(text, s["body"])


def body_ni(text, styles=None):
    s = styles or build_styles()
    return Paragraph(text, s["body_no_indent"])


def section(text, styles=None):
    s = styles or build_styles()
    return Paragraph(text, s["section_title"])


def subsection(text, styles=None):
    s = styles or build_styles()
    return Paragraph(text, s["subsection_title"])


def spacer(h=6):
    return Spacer(1, h)


class NumberedCanvas:
    """Mixin for page number and footer."""

    def __init__(self, canvas):
        self._saved_page_states = []
        self.canvas = canvas

    def __getattr__(self, name):
        return getattr(self.canvas, name)

    def saveState(self):
        self._saved_page_states.append(dict(self.canvas.__dict__))
        self.canvas.saveState()

    def restoreState(self):
        self.canvas.restoreState()

    def showPage(self):
        self._add_footer()
        self.canvas.showPage()

    def _add_footer(self):
        c = self.canvas
        c.saveState()
        page_num = c.getPageNumber()
        c.setFont(FONT_NAME, 7.5)
        c.setFillColor(FOOTER_COLOR)

        footer_line = "合成投标文件 · 公开演示专用 · 无真实数据"
        tw = stringWidth(footer_line, FONT_NAME, 7.5)
        c.drawString((PAGE_W - tw) / 2, 15 * mm, footer_line)

        page_text = f"— {page_num} —"
        pw = stringWidth(page_text, FONT_NAME, 8)
        c.drawString((PAGE_W - pw) / 2, 10 * mm, page_text)

        c.restoreState()


def build_document(output_path: Path, font_path: Path) -> None:
    register_fonts(font_path)
    styles = build_styles()

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title="合成投标演示文件",
        author="BidDeer Demo",
        subject="Synthetic Proposal - Public Demo Only",
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="main",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=frame)])
    doc.build = lambda *a, **kw: _build_with_canvas(doc, *a, **kw)

    story = _build_story(styles)

    canvasmaker_real = NumberedCanvas
    doc.build(story, canvasmaker=canvasmaker_real)


def _build_with_canvas(doc, story, canvasmaker, **kw):
    from reportlab.pdfgen import canvas

    class PatchedCanvas(NumberedCanvas):
        def __init__(self, *args, **kwargs):
            NumberedCanvas.__init__(self, canvas.Canvas(*args, **kwargs))

    doc.canvasmaker = PatchedCanvas
    BaseDocTemplate.build(doc, story, canvasmaker=PatchedCanvas, **kw)


def _build_story(styles):
    story = []
    s = styles

    # ==========================================================
    # PAGE 1: 项目概述
    # ==========================================================
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("第 1 节：项目概述", s["section_title"]))
    story.append(subsection("1.1 项目背景", s))
    story.append(body(
        "本文件为一组合成投标演示材料，用于验证 proposal-point-checker 工具在中文标书逐项检查场景中的基本功能。"
        "文件内容不对应任何真实客户、真实项目、真实招标文件或真实采购活动。所有公司名称、人员姓名、项目名称、数据字段和资质文件均为合成生成，仅供演示与测试使用。",
        s,
    ))
    story.append(body(
        "proposal-point-checker 是一款面向标书自审场景的辅助工具，能够依据用户提供的检查清单对投标文件进行逐项检索，"
        "识别每个检查项是否可以在文件中找到对应证据，并标注证据来源位置。本演示文件的设计目标是覆盖“找到”、“未找到”、“部分找到”和“证据不明确”等不同检查结果，"
        "以验证工具在实际中文标书检查中的检索能力和判断边界。",
        s,
    ))
    story.append(subsection("1.2 文件范围", s))
    story.append(body(
        "本文件围绕以下主题进行组织：项目管理说明、服务能力与资质、保密承诺、培训计划和交付计划。此外，文件包含两份合成图片附件，"
        "用于验证工具对嵌入式图片证据的 OCR 读取与字段检查能力。",
        s,
    ))
    story.append(subsection("1.3 演示边界说明", s))
    story.append(body(
        "本演示文件与工具验证的重点在于“证据是否存在”以及“证据位置是否可追溯”，而非判断投标是否通过、资质是否真实有效。"
        "所有由工具输出的结论均应由人工审核人员最终确认。工具不提供法律、合规或商业决策建议，也不对证书、营业执照、印章或签名的真实性和有效性做出任何判定。",
        s,
    ))
    story.append(subsection("1.4 本文件结构", s))
    story.append(spacer(3))
    story.append(make_table(
        ["内容模块", "所在章节", "检查用途"],
        [
            ["项目管理说明", "第 2 节", "验证是否可找到明确的项目经理任命说明"],
            ["服务能力与资质", "第 3 节", "验证营业执照注册资本图片证据检查"],
            ["保密承诺", "第 4 节", "演示模糊表述的判断边界"],
            ["培训计划", "第 5 节", "演示部分响应场景"],
            ["交付计划", "第 6 节", "演示未提供明确里程碑的场景"],
            ["图片附件", "附件 A / B", "验证 OCR 及图片证据读取能力"],
        ],
        col_widths=[110, 80, 260],
        styles=s,
    ))
    story.append(spacer(8))
    story.append(body(
        "本文件版本为演示用合成文件 v1.0。文件中出现的所有信息、数据、名称和图片均为虚构，不构成任何商业承诺或法律声明。",
        s,
    ))

    story.append(PageBreak())

    # ==========================================================
    # PAGE 2: 项目管理
    # ==========================================================
    story.append(Paragraph("第 2 节：项目管理", s["section_title"]))
    story.append(subsection("2.1 项目组织安排", s))
    story.append(body(
        "为确保项目顺利推进与高效协同，ACME Tech Solutions 将建立由项目经理统一负责的项目组织架构。"
        "项目组织涵盖项目经理、技术负责人和服务负责人三大核心角色，各角色之间通过定期沟通机制保持信息同步，"
        "确保项目目标与客户预期保持一致。",
        s,
    ))
    story.append(subsection("2.2 项目经理任命", s))
    story.append(body(
        "本项目任命张三作为项目经理，负责项目组织、沟通协调、进度跟踪和问题闭环。"
        "张三具有多年项目交付管理经验，将作为项目执行期间的主要联络人，全面协调技术、服务与客户三方之间的沟通与协作。",
        s,
    ))
    story.append(body(
        "项目经理负责制定项目计划、组织项目启动会议、跟踪任务进展、识别并推进问题解决，"
        "并在关键节点向客户汇报项目状态。在项目执行过程中，项目经理将确保各阶段目标与整体交付时间安排保持一致。",
        s,
    ))
    story.append(subsection("2.3 沟通与协调机制", s))
    story.append(body(
        "项目沟通采用定期会议与即时通讯相结合的方式进行。项目启动后将安排周例会，由项目经理主持，"
        "技术负责人和服务负责人参加，重要节点时邀请客户方相关人员参与。会议纪要将在会后一个工作日内发送至项目相关方。",
        s,
    ))
    story.append(subsection("2.4 项目过程管理", s))
    story.append(body(
        "项目团队全体成员在执行期间遵循统一的项目管理流程，包括任务分派、进度更新、问题上报和里程碑评审。"
        "所有关键过程记录将作为项目过程资产进行统一管理，确保项目信息的可追溯性。",
        s,
    ))
    story.append(spacer(4))
    story.append(make_table(
        ["角色", "人员", "职责说明"],
        [
            ["项目经理", "张三", "负责项目计划制定、沟通协调、进度跟踪和问题处理"],
            ["技术负责人", "合成示例人员 A", "负责技术方案细化、部署指导和技术问题分析"],
            ["服务负责人", "合成示例人员 B", "负责服务响应、培训支持和验收配合"],
        ],
        col_widths=[100, 140, 210],
        styles=s,
    ))
    story.append(spacer(8))
    story.append(body_ni(
        "以上人员信息为合成示例，不对应任何真实个人数据。",
        s,
    ))

    story.append(PageBreak())

    # ==========================================================
    # PAGE 3: 服务能力与资质
    # ==========================================================
    story.append(Paragraph("第 3 节：服务能力与资质", s["section_title"]))
    story.append(subsection("3.1 服务能力说明", s))
    story.append(body(
        "ACME Tech Solutions 具备丰富的技术项目实施经验，可为客户提供从方案设计、系统部署到运维支持的完整服务。"
        "公司已通过多项行业管理体系认证，并建立了标准化的项目交付流程和服务质量管理体系。",
        s,
    ))
    story.append(body(
        "公司技术团队由多名资深技术人员组成，具备跨行业、跨平台的项目实施能力。公司在信息化系统建设、"
        "数据管理平台开发、业务流程优化等领域积累了大量的项目实践经验。",
        s,
    ))
    story.append(subsection("3.2 资质材料说明", s))
    story.append(body(
        "公司持有合法有效的营业执照。营业执照演示图片见附件 A，其中可见注册资本为人民币壹佰万元。"
        "本演示检查项要求注册资本不低于人民币 100 万元，因此图片中的注册资本金额满足该阈值要求。",
        s,
    ))
    story.append(subsection("3.3 注册资本检查说明", s))
    story.append(body(
        "附件 A 中的营业执照图片显示了“注册资本：人民币壹佰万元”字段。根据检查清单中“注册资本不低于人民币 100 万元”的要求，"
        "该字段内容与要求阈值一致，系统应可识别为“已找到”对应证据。",
        s,
    ))
    story.append(subsection("3.4 图片证据边界", s))
    story.append(body(
        "附件 B 中的项目管理培训证书图片显示了“培训日期：2026-07-08”。本演示审核日期同样为 2026-07-08，"
        "因此该日期并不早于审核日期一年以上，不满足“获得日期大于 1 年”的演示检查要求。",
        s,
    ))
    story.append(spacer(4))
    story.append(make_table(
        ["检查对象", "来源位置", "可见字段", "演示判断"],
        [
            ["营业执照图片", "附件 A", "注册资本：人民币壹佰万元", "满足不低于 100 万元的演示阈值"],
            ["项目管理培训证书图片", "附件 B", "培训日期：2026-07-08", "不满足距审核日期超过 1 年的演示规则"],
        ],
        col_widths=[100, 70, 150, 130],
        styles=s,
    ))
    story.append(spacer(6))
    story.append(body_ni(
        "上述判断仅基于图片中可见文字和演示规则进行，不代表对营业执照真实性、登记状态或官方有效性的判断。"
        "所有结论均应由人工审核人员最终确认。",
        s,
    ))

    story.append(PageBreak())

    # ==========================================================
    # PAGE 4: 保密承诺
    # ==========================================================
    story.append(Paragraph("第 4 节：保密承诺", s["section_title"]))
    story.append(subsection("4.1 保密信息处理原则", s))
    story.append(body(
        "我方将按照客户要求处理与保密信息相关的事项。项目团队在实施过程中接触到客户相关信息和资料时，"
        "将遵循基本的信息处理原则，确保不向无关第三方扩散。",
        s,
    ))
    story.append(subsection("4.2 人员管理要求", s))
    story.append(body(
        "项目团队成员已接受基础数据保护意识培训，能够在项目实施过程中遵守客户现场管理要求。"
        "团队人员将在项目启动后了解客户方的信息安全管理规定，并在日常工作中参照执行。",
        s,
    ))
    story.append(subsection("4.3 数据保护意识", s))
    story.append(body(
        "涉及客户业务资料、系统配置、接口信息和运维数据的处理方式，将根据客户后续要求和合同约定进一步确认。"
        "我方建议在项目实施前与客户就信息保密范围、责任主体、操作规范和违规处理机制进行充分沟通。",
        s,
    ))
    story.append(subsection("4.4 后续协议安排", s))
    story.append(body(
        "具体保密协议、违约责任、保密期限和信息销毁要求，将在合同谈判或项目启动阶段进一步讨论。"
        "当前阶段，双方尚未就保密责任范围、违约赔偿标准和信息销毁流程达成最终共识。",
        s,
    ))
    story.append(spacer(8))
    story.append(body_ni(
        "本文件中的保密承诺表述为项目初期的原则性说明，相关内容仍需双方进一步协商确认。",
        s,
    ))

    story.append(PageBreak())

    # ==========================================================
    # PAGE 5: 培训计划
    # ==========================================================
    story.append(Paragraph("第 5 节：培训计划", s["section_title"]))
    story.append(subsection("5.1 培训目标", s))
    story.append(body(
        "培训的主要目标是确保最终用户能够熟练使用系统，具备独立完成日常操作、常见问题处理和基础维护的能力。"
        "培训内容将围绕系统核心功能展开，结合用户实际工作场景进行设计。",
        s,
    ))
    story.append(subsection("5.2 培训对象", s))
    story.append(body(
        "培训面向最终用户群体，包括系统操作人员、日常运维人员和相关业务管理人员。"
        "针对不同角色的用户，培训内容将有不同程度的侧重，以确保培训效果与实际工作需要相匹配。",
        s,
    ))
    story.append(subsection("5.3 培训内容范围", s))
    story.append(body(
        "我方将为最终用户提供培训材料，帮助用户理解系统登录、常用功能、基础操作流程和常见问题处理方式。"
        "基础操作培训将覆盖系统登录、核心功能使用、常见问题处理和服务支持联系方式。",
        s,
    ))
    story.append(body(
        "后续可根据客户需要安排补充培训，但具体培训批次、培训时长、课程大纲、考核方式和详细排期需在项目实施阶段进一步确认。",
        s,
    ))
    story.append(spacer(4))
    story.append(make_table(
        ["培训主题", "内容说明", "当前完整度"],
        [
            ["系统登录", "介绍账号登录和基本页面入口", "已简要说明"],
            ["核心功能使用", "介绍常用功能和基础操作", "已简要说明"],
            ["常见问题处理", "介绍基础问题处理方式", "已简要说明"],
            ["培训排期", "待与客户确认", "未提供明确计划"],
        ],
        col_widths=[120, 210, 120],
        styles=s,
    ))
    story.append(spacer(8))
    story.append(body_ni(
        "当前培训计划未包含具体培训批次、培训时长、课程大纲和考核方式等详细内容，属于部分响应状态。",
        s,
    ))

    story.append(PageBreak())

    # ==========================================================
    # PAGE 6: 交付计划
    # ==========================================================
    story.append(Paragraph("第 6 节：交付计划", s["section_title"]))
    story.append(subsection("6.1 交付准备", s))
    story.append(body(
        "ACME Tech Solutions 可在合同签订后启动相关准备工作，包括人员安排、资料收集、环境确认和实施沟通。"
        "合同签订将触发项目启动所需的内部资源调配和外部协调流程。",
        s,
    ))
    story.append(subsection("6.2 实施协同", s))
    story.append(body(
        "技术团队已准备开展部署与配置工作，并将在项目启动后根据客户现场环境、系统接口条件和实施窗口进一步细化工作安排。"
        "实施过程中需要客户方提供必要的环境支持、网络接入和配合人员进行协调。",
        s,
    ))
    story.append(body(
        "我方建议在正式实施前与客户方就实施环境、数据准备、接口对接等前置条件进行确认，"
        "以降低实施过程中的不确定性。",
        s,
    ))
    story.append(subsection("6.3 交付资料", s))
    story.append(body(
        "项目交付时将提供系统部署说明、用户使用手册、运维管理手册等技术文档。"
        "具体交付资料的格式、内容和交付方式将在项目实施阶段进一步确认。",
        s,
    ))
    story.append(subsection("6.4 待确认事项", s))
    story.append(body(
        "正式交付进度计划将在项目计划阶段与客户进一步协调确认。本文件当前未提供明确的阶段划分、"
        "里程碑日期、阶段验收节点或最终交付时间表。",
        s,
    ))
    story.append(spacer(4))
    story.append(make_table(
        ["交付要素", "当前说明", "是否形成明确里程碑"],
        [
            ["启动准备", "合同签订后启动准备", "否"],
            ["环境确认", "项目启动后进一步确认", "否"],
            ["部署配置", "根据现场条件安排", "否"],
            ["阶段验收", "待项目计划阶段确认", "否"],
            ["最终交付时间", "未提供明确日期", "否"],
        ],
        col_widths=[110, 190, 150],
        styles=s,
    ))
    story.append(spacer(8))
    story.append(body_ni(
        "以上交付相关说明未构成正式的交付计划或时间表。具体的阶段划分、里程碑、验收标准和交付日期均需后续协商确定。",
        s,
    ))

    story.append(PageBreak())

    # ==========================================================
    # PAGE 7: 附件 A — 营业执照图片
    # ==========================================================
    story.append(Paragraph("附件 A：营业执照图片", s["appendix_title"]))
    story.append(Paragraph(
        "以下为营业执照演示图片，用于验证 proposal-point-checker 工具是否能够从图片中读取注册资本字段，"
        "并根据检查清单要求进行金额阈值比较。",
        s["appendix_body"],
    ))
    story.append(spacer(6))

    bil_path = PICTURES_DIR / "bli.png"
    if bil_path.is_file():
        img = Image(str(bil_path), width=420, height=289)
        story.append(img)
    else:
        story.append(Paragraph(
            f"错误：未找到图片文件 {bil_path}", s["appendix_body"]
        ))

    story.append(spacer(8))
    story.append(Paragraph(
        "图片中可见注册资本为人民币壹佰万元。该金额等于人民币 100 万元，满足本演示检查项中“不低于人民币 100 万元”的要求。",
        s["appendix_body"],
    ))
    story.append(spacer(4))
    story.append(Paragraph(
        "该图片仅用于演示、测试与 OCR 验证，不代表真实营业执照、真实市场主体登记或官方认证。",
        s["boundary_note"],
    ))

    story.append(PageBreak())

    # ==========================================================
    # PAGE 8: 附件 B — 项目管理培训证书图片
    # ==========================================================
    story.append(Paragraph("附件 B：项目管理培训证书图片", s["appendix_title"]))
    story.append(Paragraph(
        "以下为项目管理培训证书演示图片，用于验证 proposal-point-checker 工具是否能够从图片中读取培训日期字段，"
        "并根据检查清单要求进行日期比较。",
        s["appendix_body"],
    ))
    story.append(spacer(6))

    pm_path = PICTURES_DIR / "PM.png"
    if pm_path.is_file():
        img = Image(str(pm_path), width=420, height=289)
        story.append(img)
    else:
        story.append(Paragraph(
            f"错误：未找到图片文件 {pm_path}", s["appendix_body"]
        ))

    story.append(spacer(8))
    story.append(Paragraph(
        "图片中可见培训日期为 2026-07-08。本演示审核日期同样为 2026-07-08，因此该日期并不早于审核日期一年以上，"
        "不满足“获得日期大于 1 年”的演示检查要求。",
        s["appendix_body"],
    ))
    story.append(spacer(4))
    story.append(Paragraph(
        "该图片仅用于演示、测试与 OCR 验证，不代表真实证书、真实资质或官方认证。",
        s["boundary_note"],
    ))

    return story


def main() -> None:
    font_path = resolve_font_path()
    print(f"Using font: {font_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "enhanced_proposal.pdf"

    build_document(output_path, font_path)

    print(f"PDF created: {output_path}")
    print(f"File size: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
