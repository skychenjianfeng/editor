"""扣件式脚手架计算书（docx）生成。"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import charts, drawing
from .scaffold_report_figures import build_scaffold_figures
from .scaffold_fastener import DEFAULTS


def _set_font(run, size: float = 10.5, bold: bool = False) -> None:
    run.font.size = Pt(size)
    run.font.name = "宋体"
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def _setup(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    for section in doc.sections:
        section.top_margin = Cm(2.2)
        section.bottom_margin = Cm(2.2)
        section.left_margin = Cm(2.6)
        section.right_margin = Cm(2.4)


def _heading(doc: Document, text: str, size: float = 14) -> None:
    p = doc.add_paragraph(style="Heading 1")
    run = p.add_run(text)
    _set_font(run, size=size, bold=True)
    run.font.color.rgb = RGBColor(0, 0, 0)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)


def _field(paragraph, code: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = code
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)


def _cover(doc: Document, meta: dict[str, str]) -> None:
    document_title = meta.get("documentTitle", "扣件式钢管脚手架计算书")
    top = doc.add_paragraph()
    top.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_font(top.add_run(f"报告编号：{meta['reportNo']}"), size=9)

    for _ in range(3):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(title.add_run(document_title), size=28, bold=True)

    en = doc.add_paragraph()
    en.alignment = WD_ALIGN_PARAGRAPH.CENTER
    english_title = (
        "CALCULATION REPORT FOR FASTENER-TYPE STEEL TUBE SCAFFOLD"
        if document_title == "扣件式钢管脚手架计算书"
        else "STRUCTURAL SAFETY CALCULATION REPORT"
    )
    _set_font(en.add_run(english_title), size=9)

    doc.add_paragraph()

    table = doc.add_table(rows=3, cols=2)
    table.autofit = False
    report_name = " ".join(
        part
        for part in (
            meta.get("projectName", "（工程名称）"),
            meta.get("moduleTitle", ""),
        )
        if part
    )
    rows = [
        ("报告名称", report_name),
        ("委托单位", meta.get("clientName", "（委托单位）")),
        ("编制单位", meta.get("orgName", "（编制单位）")),
    ]
    for i, (k, v) in enumerate(rows):
        c0, c1 = table.rows[i].cells
        c0.width = Cm(3.2)
        c1.width = Cm(11.0)
        c0.text = ""
        c1.text = ""
        _set_font(c0.paragraphs[0].add_run(k + "："), size=11, bold=True)
        _set_font(c1.paragraphs[0].add_run(v), size=11)

    for _ in range(2):
        doc.add_paragraph()

    sign = doc.add_table(rows=2, cols=3)
    sign.style = "Table Grid"
    heads = ["编制", "审核", "批准"]
    for j, h in enumerate(heads):
        cell = sign.rows[0].cells[j]
        cell.text = ""
        _set_font(cell.paragraphs[0].add_run(h), size=10, bold=True)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell2 = sign.rows[1].cells[j]
        cell2.text = ""
        _set_font(cell2.paragraphs[0].add_run("\n\n签字：            日期："), size=9)

    for _ in range(3):
        doc.add_paragraph()
    bottom = doc.add_paragraph()
    bottom.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(bottom.add_run(meta.get("orgName", "（编制单位）")), size=13, bold=True)
    date = doc.add_paragraph()
    date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(date.add_run(meta.get("date", "")), size=10)
    doc.add_page_break()


def _declaration(doc: Document) -> None:
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(t.add_run("声  明"), size=18, bold=True)
    doc.add_paragraph()

    items = [
        "本计算书须经编制、审核、批准人员签署后方为有效。",
        "本计算书无编制单位盖章无效。",
        "本计算书涂改无效。",
        "未经编制单位书面批准，不得部分复制本计算书。",
        "本计算书仅对委托方提供的参数与工况负责，参数真实性由委托方负责。",
        "本计算书为结构验算文件，不替代专项施工方案；施工尚应符合现行规范与专项方案要求。",
        "本计算书解释权归编制单位所有。",
    ]
    for i, text in enumerate(items, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.space_after = Pt(6)
        _set_font(p.add_run(f"{i}. {text}"), size=10.5)
    doc.add_page_break()


def _toc(doc: Document) -> None:
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(t.add_run("目  录"), size=18, bold=True)
    doc.add_paragraph()
    p = doc.add_paragraph()
    _field(p, 'TOC \\o "1-2" \\h \\z \\u')
    doc.add_page_break()


def _header_footer(section, meta: dict[str, str]) -> None:
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False

    hp = section.header.paragraphs[0]
    hp.text = ""
    _set_font(
        hp.add_run(meta.get("documentTitle", "扣件式钢管脚手架计算书")),
        size=8,
    )
    hp.add_run("\t\t")
    _set_font(hp.add_run(f"报告编号：{meta['reportNo']}"), size=8)

    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.text = ""
    _set_font(fp.add_run("第 "), size=8)
    _field(fp, " PAGE ")
    _set_font(fp.add_run(" 页 共 "), size=8)
    _field(fp, " NUMPAGES ")
    _set_font(fp.add_run(" 页"), size=8)


def _table(doc: Document, header: list[str], rows: list[list[str]], widths: list[float] | None = None) -> None:
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    for i, text in enumerate(header):
        cell = table.rows[0].cells[i]
        cell.text = ""
        _set_font(cell.paragraphs[0].add_run(text), bold=True)
    for row in rows:
        cells = table.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = ""
            _set_font(cells[i].paragraphs[0].add_run(str(text)))
    if widths:
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    # 表头跨页重复
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


GREATER_OR_EQUAL_RESULT_KEYS = {
    "anchor_overturning",
    "counterweight_requirement",
    "suspension_stability",
    "wire_rope_safety",
}


def _failed_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Use the result rows as the source of truth; summaries can be stale."""
    return [result for result in payload.get("results", []) if not result.get("ok", False)]


def _conclusion_text(payload: dict[str, Any]) -> str:
    failed = _failed_results(payload)
    if not failed:
        return "本次验算全部项满足规范要求。"
    failed_items = "、".join(result["item"] for result in failed)
    return (
        f"本次验算共 {len(payload.get('results', []))} 项，"
        f"其中 {len(failed)} 项不满足：{failed_items}。"
    )


def _format_number(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(numeric)) if numeric.is_integer() else str(value)


def _result_outcome_text(result: dict[str, Any]) -> str:
    verdict = "满足要求" if result["ok"] else "不满足要求"
    if result.get("unit") == "通过项/检查项":
        return (
            f"结果：通过 {_format_number(result['value'])}/"
            f"{_format_number(result['limit'])} 项 → {verdict}"
        )

    value = result["value"]
    limit = result["limit"]
    if value == limit:
        relation = "="
    elif result.get("key") in GREATER_OR_EQUAL_RESULT_KEYS:
        relation = "≥" if result["ok"] else "<"
    else:
        relation = "≤" if result["ok"] else ">"
    return (
        f"结果：{_format_number(value)} {result['unit']} {relation} "
        f"{_format_number(limit)} → {verdict}"
    )


PARAM_LABELS: dict[str, tuple[str, str]] = {
    "h": ("步距 h", "m"),
    "la": ("立杆纵距 la", "m"),
    "lb": ("立杆横距 lb", "m"),
    "H": ("搭设高度 H", "m"),
    "steel": ("钢管类型", "—"),
    "tie": ("连墙件布置", "—"),
    "layout": ("单/双排", "—"),
    "scaffoldType": ("架体类型", "—"),
    "board": ("脚手板类型", "—"),
    "dead": ("脚手板自重", "kN/m²"),
    "live": ("施工均布活荷载", "kN/m²"),
    "wind": ("基本风压 w0", "kN/m²"),
    "z": ("风压计算高度 z", "m"),
    "terrain": ("地面粗糙度", "—"),
    "enclosure": ("脚手架封闭状况", "—"),
    "backdrop": ("背靠建筑物状况", "—"),
    "phiWind": ("挡风系数 φ", "—"),
    "foundation": ("地基类型", "—"),
    "fg": ("地基承载力特征值 fg", "kPa"),
    "baseArea": ("垫板底面积", "m²"),
    "hBoard": ("挡脚板高度", "mm"),
    "braceW": ("剪刀撑宽度", "m"),
    "tieNv": ("连墙件连接承载力 Nv", "kN"),
    "tieOffset": ("连墙件偏离主节点", "mm"),
    "tieFromFirstStep": ("首步设置连墙件", "—"),
    "tieLength": ("连墙件计算长度", "m"),
    "tieVerticalSpacing": ("连墙件竖向间距", "m"),
    "tieHorizontalSpacing": ("连墙件水平间距", "m"),
    "connectionType": ("连墙件连接方式", "—"),
    "tieArrangement": ("连墙件布置形式", "—"),
    "sweepBar": ("设置纵横向扫地杆", "—"),
    "sweepBarHeight": ("扫地杆距钢管底端", "mm"),
    "railHeight": ("防护栏杆上杆高度", "m"),
    "safetyNet": ("张挂密目式安全立网", "—"),
    "freeHeight": ("连墙点以上悬臂高度", "m"),
    "braceSpacing": ("剪刀撑间距（H<24m）", "m"),
    "braceContinuous": ("H≥24m 全立面连续剪刀撑", "—"),
    "gamma0": ("结构重要性系数 γ0", "—"),
    "tieNetArea": ("连墙件净截面面积 Ac", "mm²"),
    "boardThickness": ("脚手板厚度", "mm"),
    "boardF": ("脚手板抗弯强度设计值", "N/mm²"),
    "boardE": ("脚手板弹性模量", "N/mm²"),
}


def build_docx(
    params: dict[str, Any],
    payload: dict[str, Any],
    meta: dict[str, str] | None = None,
) -> bytes:
    params = {**DEFAULTS, **(params or {})}
    meta = {
        "reportNo": f"PM-CALC-{datetime.now():%Y%m%d}-001",
        "projectName": "（工程名称）",
        "clientName": "（委托单位）",
        "orgName": "（编制单位）",
        "date": f"{datetime.now():%Y年%m月%d日}",
        **(meta or {}),
    }
    doc = Document()
    _setup(doc)
    _cover(doc, meta)
    _declaration(doc)
    _toc(doc)
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    _header_footer(section, meta)

    if not payload.get("verified", False):
        warn = doc.add_paragraph()
        _set_font(
            warn.add_run(
                f"编制说明：本计算书由自研计算内核生成（{datetime.now():%Y-%m-%d %H:%M}），"
                "部分系数仍待与品茗 oracle 复核（verified=false）。"
            ),
            size=9,
        )

    _heading(doc, "计算依据", size=12)
    standards = payload.get("standards") or {}
    applied = standards.get("applied") or []
    missing = standards.get("missing") or []
    for i, standard in enumerate(applied, start=1):
        para = doc.add_paragraph()
        _set_font(para.add_run(f"{i}、《{standard['name']}》{standard['code']}"), size=9.5)
    if missing:
        note = doc.add_paragraph()
        _set_font(
            note.add_run(
                "本版未覆盖（本地库缺书，待补库后复核）："
                + "；".join(f"《{m['name']}》{m['code']}" for m in missing)
            ),
            size=9,
        )
    gaps = standards.get("gaps") or []
    if gaps:
        note = doc.add_paragraph()
        _set_font(note.add_run("适用边界说明：" + "；".join(gaps)), size=9)

    _heading(doc, "一、计算参数")
    rows = []
    for key, (label, unit) in PARAM_LABELS.items():
        if key in params:
            rows.append([label, str(params[key]), unit])
    _table(doc, ["参数", "取值", "单位"], rows, widths=[7.0, 5.0, 3.0])

    _heading(doc, "二、计算简图")
    figures = [
        (drawing.export_png(params, "elevation", dark=False), "图 1  脚手架正立面计算简图", {"height": Cm(19.5)}),
        (drawing.export_png(params, "plan", dark=False), "图 2  脚手架平面布置图", {"width": Cm(14.6)}),
    ]
    for png, caption, size in figures:
        doc.add_picture(io.BytesIO(png), **size)
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_font(cap.add_run(caption), size=8.5)

    _heading(doc, "三、截面与主要计算量")
    d = payload.get("derived", {})
    derived_rows = [
        ["截面面积 A", f"{d.get('A_mm2', 0):.1f}", "mm²"],
        ["回转半径 i", f"{d.get('i_mm', 0):.2f}", "mm"],
        ["截面模量 W", f"{d.get('W_mm3', 0):.0f}", "mm³"],
        ["长细比 λ（验算，k=1）", f"{d.get('lambda_check', 0):.1f}", "—"],
        ["长细比 λ（稳定，k=1.155）", f"{d.get('lambda_stability', 0):.1f}", "—"],
        ["稳定系数 φ", f"{d.get('phi', 0):.3f}", "—"],
        ["计算长度系数 μ", f"{d.get('mu', 0):.2f}", "—"],
        ["立杆自重 gk", f"{d.get('gk_kN_m', 0):.4f}", "kN/m"],
        ["风压高度系数 μz", f"{d.get('muz', 0):.3f}", "—"],
        ["体型系数 μs", f"{d.get('mus', 0):.3f}", "—"],
        ["风荷载标准值 wk", f"{d.get('wk_kN_m2', 0):.3f}", "kN/m²"],
        ["轴力设计值 N", f"{d.get('N_kN', 0):.2f}", "kN"],
        ["轴力标准值 Nk", f"{d.get('Nk_kN', 0):.2f}", "kN"],
        ["风弯矩 Mw", f"{d.get('Mw_Nmm', 0):.0f}", "N·mm"],
    ]
    _table(doc, ["项目", "数值", "单位"], derived_rows, widths=[7.5, 4.5, 3.0])

    d = payload.get("derived", {})
    dead = float(params.get("dead", 0.35))
    live = float(params.get("live", 2.0))
    la = float(params.get("la", 1.5))
    lb = float(params.get("lb", 0.9))
    H = float(params.get("H", 24))
    q_long = 1.2 * (dead * lb / 2) + 1.4 * (live * lb / 2)
    q_trans = 1.2 * (dead * la / 2) + 1.4 * (live * la / 2)
    EI = 206000.0 * float(d.get("I_mm4", 0) or 1)

    _heading(doc, "四、内力与变形图")

    def _figure(png: bytes, caption: str) -> None:
        doc.add_picture(io.BytesIO(png), width=Cm(15.2))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_font(cap.add_run(caption), size=8.5)

    _figure(
        charts.beam_diagrams(q_long, la, EI, "continuous", f"纵向水平杆 q={q_long:.2f} kN/m"),
        "图 3  纵向水平杆（三跨连续梁）弯矩、剪力与挠度",
    )
    _figure(
        charts.beam_diagrams(q_trans, lb, EI, "simple", f"横向水平杆 q={q_trans:.2f} kN/m"),
        "图 4  横向水平杆（简支梁）弯矩、剪力与挠度",
    )
    _figure(
        charts.column_diagrams(float(d.get("N_kN", 0)), float(d.get("Mw_Nmm", 0)) / 1e6, H),
        "图 5  立杆轴力图与风弯矩图",
    )

    _heading(doc, "五、计算过程")

    def _substitutions(result: dict[str, Any]) -> str:
        key = result["key"]
        values = {
            "upright_stability": (
                f"N={d.get('N_kN')}kN，φ={d.get('phi')}，A={d.get('A_mm2')}mm²，"
                f"Mw={d.get('Mw_Nmm')}N·mm，W={d.get('W_mm3')}mm³"
            ),
            "slenderness": f"μ={d.get('mu')}，h={params.get('h', 1.8)}m，i={d.get('i_mm')}mm（验算取 k=1）",
            "tie_strength": f"Nl={d.get('Nl_kN')}kN，Ac=A={d.get('A_mm2')}mm²，0.85f={0.85 * 205:.2f}N/mm²",
            "tie_stability": f"Nl={d.get('Nl_kN')}kN，φ={d.get('phi')}，A={d.get('A_mm2')}mm²",
            "ledger_long": f"q={d.get('q_long_kN_m')}kN/m，la={params.get('la', 1.5)}m，W={d.get('W_mm3')}mm³",
            "ledger_trans": f"q={d.get('q_trans_kN_m')}kN/m，lb={params.get('lb', 0.9)}m，W={d.get('W_mm3')}mm³",
            "coupler_slip": f"R={d.get('R_kN')}kN，Rc=8.00kN（表 5.1.7）",
            "foundation": f"Nk={d.get('Nk_kN')}kN，A={params.get('baseArea', 0.25)}m²，fg={d.get('fg_kPa')}kPa",
            "height_limit": f"H={params.get('H', 24)}m，限值 50m（双排）",
            "construct_limit": f"h={params.get('h', 1.8)}m/2.0，la={params.get('la', 1.5)}m/1.8",
            "tie_area": f"Aw = {params.get('tie', '两步三跨')} 覆盖面积 = {d.get('Aw_m2')}m²",
            "tie_connection": f"Nl={d.get('Nl_kN')}kN，Nv={d.get('tieNv_kN')}kN",
            "tie_offset": f"偏移 {params.get('tieOffset', 200)}mm，限值 300mm",
            "tie_first_step": f"方案设置：{params.get('tieFromFirstStep', '是')}",
            "sweep_bar": f"设置：{params.get('sweepBar', '是')}；距底端 {params.get('sweepBarHeight', 200)}mm",
            "brace_angle": f"tanα = h/la = {params.get('h', 1.8)}/{params.get('la', 1.5)}",
            "rail_height": f"上杆高度 {params.get('railHeight', 1.2)}m",
            "toe_board": f"挡脚板高度 {params.get('hBoard', 180)}mm",
            "safety_net": f"方案设置：{params.get('safetyNet', '是')}",
        }
        return values.get(key, "")

    for result in payload.get("results", []):
        head = doc.add_paragraph()
        head.paragraph_format.space_before = Pt(8)
        head.paragraph_format.space_after = Pt(2)
        _set_font(head.add_run(f"{result['no']}. {result['item']}"), size=11, bold=True)
        _set_font(head.add_run(f"（{result['clause']}）"), size=9)

        formula = doc.add_paragraph()
        formula.paragraph_format.space_after = Pt(1)
        _set_font(formula.add_run(f"公式：{result['detail']}"), size=9.5)

        substitution_text = _substitutions(result)
        if substitution_text:
            substitution = doc.add_paragraph()
            substitution.paragraph_format.space_after = Pt(1)
            _set_font(substitution.add_run(f"代入：{substitution_text}"), size=9.5)

        outcome = doc.add_paragraph()
        if result["key"] in {"tie_first_step", "sweep_bar", "safety_net"}:
            outcome_text = f"结果：{'是' if result['ok'] else '否'} → {'满足要求' if result['ok'] else '不满足要求'}"
        elif result["key"] == "brace_angle":
            outcome_text = (
                f"结果：45° ≤ {result['value']}° ≤ 60° → {'满足要求' if result['ok'] else '不满足要求'}"
            )
        elif result["key"] in {"rail_height", "toe_board"}:
            outcome_text = (
                f"结果：{result['value']} {result['unit']} "
                f"{'≥' if result['ok'] else '<'} {result['limit']} → {'满足要求' if result['ok'] else '不满足要求'}"
            )
        else:
            outcome_text = (
                f"结果：{result['value']} {result['unit']} "
                f"{'≤' if result['ok'] else '>'} {result['limit']} → {'满足要求' if result['ok'] else '不满足要求'}"
            )
        _set_font(outcome.add_run(outcome_text), size=9.5, bold=not result["ok"])

    _heading(doc, "六、验算结果")
    result_rows = []
    for r in payload.get("results", []):
        result_rows.append(
            [
                str(r["no"]),
                r["item"],
                f"{r['value']}",
                f"{r['limit']}",
                f"{r['ratio'] * 100:.0f}%",
                "通过" if r["ok"] else "不满足",
                r["clause"],
            ]
        )
    _table(
        doc,
        ["项次", "计算项", "计算值", "限值", "利用率", "判定", "规范条文"],
        result_rows,
        widths=[1.2, 5.2, 2.2, 2.0, 1.8, 1.8, 4.4],
    )

    _heading(doc, "七、结论")
    p = doc.add_paragraph()
    _set_font(p.add_run(_conclusion_text(payload)))

    assumptions = payload.get("assumptions", [])
    if assumptions:
        _heading(doc, "八、计算说明与待核对项")
        for text in assumptions:
            item = doc.add_paragraph(style="List Bullet")
            _set_font(item.add_run(text), size=9.5)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def build_generic_docx(
    params: dict[str, Any],
    payload: dict[str, Any],
    meta: dict[str, str] | None = None,
) -> bytes:
    """通用模块计算书：参数 + 计算过程 + 结果 + 结论（无脚手架专用图表）。"""
    params = payload.get("params") or params or {}
    meta = {
        "reportNo": f"PM-CALC-{datetime.now():%Y%m%d}-001",
        "projectName": "（工程名称）",
        "clientName": "（委托单位）",
        "orgName": "（编制单位）",
        "date": f"{datetime.now():%Y年%m月%d日}",
        **(meta or {}),
    }
    doc = Document()
    _setup(doc)
    _cover(doc, meta)
    _declaration(doc)
    _toc(doc)
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    _header_footer(section, meta)

    _heading(doc, "计算依据", size=12)
    for i, standard in enumerate((payload.get("standards") or {}).get("applied", []), start=1):
        p = doc.add_paragraph()
        _set_font(p.add_run(f"{i}、《{standard['name']}》{standard['code']}"), size=9.5)

    _heading(doc, "一、计算参数")
    include_unit = any(
        PARAM_LABELS.get(key, (key, ""))[1]
        for key in params
    )
    rows = []
    for key, value in params.items():
        label, unit = PARAM_LABELS.get(key, (key, ""))
        rows.append([label, str(value), unit] if include_unit else [label, str(value)])
    if include_unit:
        _table(doc, ["参数", "取值", "单位"], rows, widths=[7.0, 5.0, 3.0])
    else:
        _table(doc, ["参数", "取值"], rows, widths=[8.0, 6.0])

    _heading(doc, "二、计算过程")
    for r in payload.get("results", []):
        head = doc.add_paragraph()
        head.paragraph_format.space_before = Pt(8)
        _set_font(head.add_run(f"{r['no']}. {r['item']}"), size=11, bold=True)
        _set_font(head.add_run(f"（{r['clause']}）"), size=9)
        formula = doc.add_paragraph()
        _set_font(formula.add_run(f"公式：{r['detail']}"), size=9.5)
        outcome = doc.add_paragraph()
        _set_font(
            outcome.add_run(_result_outcome_text(r)),
            size=9.5,
            bold=not r["ok"],
        )

    figures = build_scaffold_figures(meta.get("moduleKey", ""), payload)
    if figures:
        _heading(doc, "三、内力与变形图")
        for index, (png, caption) in enumerate(figures, start=1):
            doc.add_picture(io.BytesIO(png), width=Cm(15.2))
            cap = doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _set_font(cap.add_run(f"图 {index}  {caption}"), size=8.5)

    _heading(doc, "四、验算结果" if figures else "三、验算结果")
    result_rows = [
        [str(r["no"]), r["item"], str(r["value"]), str(r["limit"]), f"{r['ratio']*100:.0f}%",
         "满足要求" if r["ok"] else "不满足要求", r["clause"]]
        for r in payload.get("results", [])
    ]
    _table(doc, ["项次", "计算项", "计算值", "限值", "利用率", "判定", "规范条文"], result_rows,
           widths=[1.2, 4.8, 2.2, 2.0, 1.8, 2.2, 4.2])

    _heading(doc, "五、结论" if figures else "四、结论")
    p = doc.add_paragraph()
    _set_font(p.add_run(_conclusion_text(payload)))

    assumptions = payload.get("assumptions") or []
    if assumptions:
        _heading(doc, "六、计算说明" if figures else "五、计算说明")
        for a in assumptions:
            item = doc.add_paragraph(style="List Bullet")
            _set_font(item.add_run(a), size=9.5)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
