#!/usr/bin/env python3
"""
render_diagnostic.py — Rapport de diagnostic structurel IC Ingénieurs.

Génère un DOCX complet programmatiquement (python-docx).
Aucun template, aucune balise Jinja2.

Usage:
    python render_diagnostic.py context.json [--photos-dir ./photos] [--output rapport.docx]

Formats d'entrée acceptés:
  - IC direct  : disorders[] avec ref/name/location/description/ie/cause/recommendations/photos
  - Edifice    : observations[] avec ref/name/localisation/zone/observation/ie/action/photos
"""

import argparse
import io
import json
import os
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor
from lxml import etree

# IC Ingénieurs brand
IC_BLUE = RGBColor(0x1F, 0x3A, 0x5F)
IC_BLUE_HEX = "1F3A5F"
IC_ORANGE = RGBColor(0xE8, 0x6A, 0x1A)
IC_ROW_ALT = "F0F4F8"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"

# IE scale: (background hex, text label)
IE_COLORS = {
    1: ("C00000", "Critique"),
    2: ("E86A1A", "Mauvais état"),
    3: ("D4A017", "État moyen"),
    4: ("4CAF50", "Bon état"),
    5: ("1F7A3A", "Très bon état"),
}

# IE methodology table data
IE_TABLE_ROWS = [
    ("1", "C00000", "Désordres mécaniques graves – Risque de ruine immédiate",
     "Problème de sécurité immédiate", "Mise en sécurité immédiate", "Curatif", "Immédiat"),
    ("2", "E86A1A", "Désordres mécaniques graves sans risque de ruine immédiate",
     "Situation créant des difficultés d'exploitation", "Renforcement ou réparation", "Curatif", "Court terme"),
    ("3", "D4A017", "Dégradation des matériaux ou désordres mécaniques sans gravité",
     "Situation créant des difficultés d'inconfort ou de gêne à l'exploitation",
     "Entretien spécialisé ou réparation", "Préventif", "Moyen terme"),
    ("4", "4CAF50", "Bon état structurel",
     "Bon état des éléments d'usage", "Entretien courant", "", "Long terme"),
    ("-", "AAAAAA", "Non évalué", "", "", "", ""),
]

MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

SCRIPT_DIR = Path(__file__).resolve().parent
IC_LOGO = SCRIPT_DIR.parent.parent / "agent/document-generator/organizations/ic-ingenieurs/LogoIC.webp"


def format_date_french(iso: str) -> str:
    try:
        dt = datetime.strptime(iso[:10], "%Y-%m-%d")
        return f"{dt.day} {MOIS_FR[dt.month - 1]} {dt.year}"
    except (ValueError, TypeError):
        return iso or ""


def format_date_short(iso: str) -> str:
    try:
        dt = datetime.strptime(iso[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return iso or ""


# ── XML helpers ───────────────────────────────────────────────────────────────

def set_cell_shading(cell, color: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}" w:val="clear"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_margins(cell, top=50, bottom=50, left=100, right=100) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:start w:w="{left}" w:type="dxa"/>'
        f'<w:end w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def set_table_borders(table, color: str = "AAAAAA") -> None:
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(f'<w:tblPr {nsdecls("w")}/>')
        tbl.insert(0, tblPr)
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def merge_cells_horizontal(row, start_col: int, end_col: int) -> None:
    """Merge cells in a row from start_col to end_col (inclusive)."""
    cells = row.cells
    for i in range(start_col + 1, end_col + 1):
        cells[start_col].merge(cells[i])


# ── Heading styles with auto-numbering ────────────────────────────────────────

def setup_heading_styles(doc: Document) -> int:
    """
    Add multilevel decimal numbering to the existing numbering part and
    configure Heading 1 (level 0) and Heading 2 (level 1) with IC blue.

    Returns the numId assigned (to use when overriding per-paragraph if needed).
    """
    np_part = doc.part.numbering_part
    root = np_part._element

    # Find next free IDs
    existing_abstract = [
        int(el.get(f"{W}abstractNumId"))
        for el in root.findall(f"{W}abstractNum")
        if el.get(f"{W}abstractNumId") is not None
    ]
    existing_nums = [
        int(el.get(f"{W}numId"))
        for el in root.findall(f"{W}num")
        if el.get(f"{W}numId") is not None
    ]
    new_abstract_id = max(existing_abstract, default=-1) + 1
    new_num_id = max(existing_nums, default=0) + 1

    # Build abstractNum element
    aNum = etree.SubElement(root, f"{W}abstractNum")
    aNum.set(f"{W}abstractNumId", str(new_abstract_id))
    mlt = etree.SubElement(aNum, f"{W}multiLevelType")
    mlt.set(f"{W}val", "multilevel")

    level_defs = [
        (0, "%1",       "0",    "0"),
        (1, "%1.%2",    "720",  "360"),
        (2, "%1.%2.%3", "1080", "360"),
    ]
    for ilvl, lvl_text, left, hanging in level_defs:
        lvl = etree.SubElement(aNum, f"{W}lvl")
        lvl.set(f"{W}ilvl", str(ilvl))
        for tag, val in [
            ("start", "1"), ("numFmt", "decimal"),
            ("lvlText", lvl_text), ("lvlJc", "left"),
        ]:
            el = etree.SubElement(lvl, f"{W}{tag}")
            el.set(f"{W}val", val)
        pPr = etree.SubElement(lvl, f"{W}pPr")
        ind = etree.SubElement(pPr, f"{W}ind")
        ind.set(f"{W}left", left)
        ind.set(f"{W}hanging", hanging)

    # Concrete num → references abstractNum
    num_el = etree.SubElement(root, f"{W}num")
    num_el.set(f"{W}numId", str(new_num_id))
    aNumId = etree.SubElement(num_el, f"{W}abstractNumId")
    aNumId.set(f"{W}val", str(new_abstract_id))

    # Style Heading 1
    h1 = doc.styles["Heading 1"]
    h1.font.color.rgb = IC_BLUE
    h1.font.size = Pt(14)
    h1.font.bold = True
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(4)
    _set_style_numpr(h1, new_num_id, ilvl=0)

    # Style Heading 2
    h2 = doc.styles["Heading 2"]
    h2.font.color.rgb = IC_BLUE
    h2.font.size = Pt(12)
    h2.font.bold = False
    h2.paragraph_format.space_before = Pt(8)
    h2.paragraph_format.space_after = Pt(2)
    _set_style_numpr(h2, new_num_id, ilvl=1)

    return new_num_id


def _set_style_numpr(style, num_id: int, ilvl: int) -> None:
    """Attach numbering (numId, ilvl) to a paragraph style."""
    pPr = style.element.get_or_add_pPr()
    existing = pPr.find(f"{W}numPr")
    if existing is not None:
        pPr.remove(existing)
    numPr = etree.SubElement(pPr, f"{W}numPr")
    etree.SubElement(numPr, f"{W}ilvl").set(f"{W}val", str(ilvl))
    etree.SubElement(numPr, f"{W}numId").set(f"{W}val", str(num_id))


# ── Photo handling ─────────────────────────────────────────────────────────────

def _load_photo_buf(photo_path: str, max_width_cm: float = 8.0):
    """Return (BytesIO, width_cm) with EXIF rotation applied.
    Falls back to raw bytes if Pillow unavailable."""
    try:
        from PIL import Image, ExifTags
        with Image.open(photo_path) as img:
            try:
                exif = img._getexif()
                if exif:
                    for tag, val in exif.items():
                        if ExifTags.TAGS.get(tag) == "Orientation":
                            if val == 3:
                                img = img.rotate(180, expand=True)
                            elif val == 6:
                                img = img.rotate(270, expand=True)
                            elif val == 8:
                                img = img.rotate(90, expand=True)
                            break
            except Exception:
                pass
            max_px = 1200
            w, h = img.size
            if max(w, h) > max_px:
                scale = max_px / max(w, h)
                img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=80, optimize=True)
            buf.seek(0)
            return buf, max_width_cm
    except ImportError:
        try:
            return io.BytesIO(open(photo_path, "rb").read()), max_width_cm
        except Exception:
            return None, None
    except Exception:
        return None, None


def add_photo_to_cell(cell, photo_path: str, max_width_cm: float = 7.5) -> bool:
    if not photo_path or not os.path.exists(photo_path):
        r = cell.paragraphs[0].add_run("[photo manquante]")
        r.font.size = Pt(7)
        r.font.italic = True
        r.font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)
        return False
    buf, width_cm = _load_photo_buf(photo_path, max_width_cm)
    if buf is None:
        r = cell.paragraphs[0].add_run("[photo non disponible]")
        r.font.size = Pt(7)
        r.font.italic = True
        return False
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(buf, width=Cm(width_cm))
    return True


# ── Cover page ────────────────────────────────────────────────────────────────

def build_cover(doc: Document, ctx: dict) -> None:
    """Page de garde style IC Ingénieurs."""
    for _ in range(6):
        doc.add_paragraph()

    # Main title
    titre = ctx.get("titre_service") or ctx.get("project_name") or "Diagnostic Structurel"
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = tp.add_run(titre)
    tr.font.size = Pt(22)
    tr.font.color.rgb = IC_BLUE

    doc.add_paragraph()

    # Client
    client = ctx.get("client") or "A remplir"
    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.add_run("Client : ").font.size = Pt(13)
    cp.runs[0].font.color.rgb = IC_BLUE
    cr = cp.add_run(client)
    cr.font.size = Pt(13)

    # Chantier / résidence
    residence = ctx.get("residence") or ""
    if residence:
        rp = doc.add_paragraph()
        rp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rr = rp.add_run("Chantier :")
        rr.font.size = Pt(13)
        rr.font.color.rgb = IC_BLUE
        rp2 = doc.add_paragraph()
        rp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rr2 = rp2.add_run(residence)
        rr2.font.size = Pt(13)

    # Address
    adresse = ctx.get("adresse") or ""
    if adresse:
        doc.add_paragraph()
        ap = doc.add_paragraph()
        ap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ar = ap.add_run(adresse)
        ar.font.size = Pt(15)
        ar.font.bold = True

    doc.add_paragraph()
    doc.add_paragraph()

    # Date
    date_str = format_date_short(ctx.get("date_visite") or ctx.get("date_rapport") or "")
    if date_str:
        dp = doc.add_paragraph()
        dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        dp.paragraph_format.space_after = Pt(6)
        dr = dp.add_run(f"du {date_str}")
        dr.font.size = Pt(9)

    # Validation table
    etabli_par = ctx.get("etabli_par") or "R. Laborbe"
    val_tbl = doc.add_table(rows=3, cols=4)
    val_tbl.style = "Table Grid"
    set_table_borders(val_tbl, "888888")

    headers = ["Rapport\nétabli par :", "Etabli Le :", "Signature", "Remarques"]
    for cell, h in zip(val_tbl.rows[0].cells, headers):
        cell.text = h
        if cell.paragraphs[0].runs:
            r = cell.paragraphs[0].runs[0]
            r.font.size = Pt(8)
            r.font.bold = True
        set_cell_margins(cell, 40, 40, 60, 60)

    data_row = val_tbl.rows[1]
    data_row.cells[0].text = etabli_par
    data_row.cells[1].text = date_str
    data_row.cells[2].text = ""  # signature placeholder
    data_row.cells[3].text = ""
    for cell in data_row.cells:
        if cell.paragraphs[0].runs:
            cell.paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_margins(cell, 40, 40, 60, 60)

    # Empty validation row
    for cell in val_tbl.rows[2].cells:
        cell.text = ""
        set_cell_margins(cell, 30, 30, 60, 60)

    # Footer bar with IC info
    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()

    footer_tbl = doc.add_table(rows=1, cols=2)
    footer_tbl.style = "Table Grid"

    # Thin top border line only
    ft = footer_tbl._tbl
    ftPr = ft.tblPr
    if ftPr is None:
        ftPr = parse_xml(f'<w:tblPr {nsdecls("w")}/>')
        ft.insert(0, ftPr)
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="888888"/>'
        f'<w:left w:val="none"/><w:bottom w:val="none"/>'
        f'<w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    ftPr.append(borders)

    left_cell = footer_tbl.rows[0].cells[0]
    right_cell = footer_tbl.rows[0].cells[1]
    set_cell_margins(left_cell, 60, 60, 60, 60)
    set_cell_margins(right_cell, 60, 60, 60, 60)

    # Logo + firm name in left cell
    logo_path = IC_LOGO
    if logo_path.exists():
        try:
            from PIL import Image
            with Image.open(str(logo_path)) as img:
                buf = io.BytesIO()
                img.convert("RGB").save(buf, format="JPEG", quality=90)
                buf.seek(0)
            lp = left_cell.paragraphs[0]
            lp.add_run().add_picture(buf, height=Cm(0.9))
            lp.add_run("  I.C. Ingénieurs Conseils").font.size = Pt(9)
        except Exception:
            left_cell.paragraphs[0].add_run("I.C. Ingénieurs Conseils").font.size = Pt(9)
    else:
        left_cell.paragraphs[0].add_run("I.C. Ingénieurs Conseils").font.size = Pt(9)
    if left_cell.paragraphs[0].runs:
        for run in left_cell.paragraphs[0].runs:
            run.font.color.rgb = IC_BLUE

    # Contact info in right cell
    right_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    contacts = "08.53.16.89.98\ndelaby.lo@gmail.com\n145 Boulevard de Magenta\n75010 Paris"
    for line in contacts.split("\n"):
        p = right_cell.add_paragraph() if right_cell.paragraphs[0].runs else right_cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run(line)
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    doc.add_page_break()


# ── Sections ──────────────────────────────────────────────────────────────────

def build_section_batiment(doc: Document, ctx: dict) -> None:
    doc.add_heading("Présentation du bâtiment", level=1)

    building = ctx.get("building") or {}
    rows = [
        ("Nom / Résidence", building.get("name") or ctx.get("residence") or ""),
        ("Adresse", building.get("address") or ctx.get("adresse") or ""),
        ("Type de structure", building.get("type") or ctx.get("construction_type") or ""),
        ("Année de construction", building.get("year") or ctx.get("construction_era") or ""),
        ("Nombre d'étages", ctx.get("n_etage") or ""),
        ("Utilisation", ctx.get("utilisation") or ""),
    ]
    rows = [(l, v) for l, v in rows if v]

    if rows:
        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"
        set_table_borders(table, "CCCCCC")
        for cell, h in zip(table.rows[0].cells, ["Caractéristique", "Information"]):
            cell.text = h
            set_cell_shading(cell, IC_BLUE_HEX)
            if cell.paragraphs[0].runs:
                r = cell.paragraphs[0].runs[0]
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                r.font.bold = True
                r.font.size = Pt(9)
            set_cell_margins(cell, 40, 40, 80, 80)

        for i, (label, value) in enumerate(rows):
            row = table.add_row()
            row.cells[0].text = label
            row.cells[1].text = str(value)
            for j, cell in enumerate(row.cells):
                if cell.paragraphs[0].runs:
                    r = cell.paragraphs[0].runs[0]
                    r.font.size = Pt(9)
                    if j == 0:
                        r.font.bold = True
                        r.font.color.rgb = IC_BLUE
                set_cell_margins(cell, 40, 40, 80, 80)
                if i % 2 == 0:
                    set_cell_shading(cell, IC_ROW_ALT)

    desc = building.get("description") or ctx.get("description_batiment") or ""
    if desc:
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        rl = p.add_run("Description : ")
        rl.font.bold = True
        rl.font.size = Pt(9)
        rl.font.color.rgb = IC_BLUE
        rv = p.add_run(desc)
        rv.font.size = Pt(9)

    doc.add_paragraph()


def build_section_contexte(doc: Document, ctx: dict) -> None:
    doc.add_heading("Contexte de la mission", level=1)
    text = ctx.get("contexte") or ctx.get("objet_visite") or ""
    if text:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.add_run(text).font.size = Pt(9)
    doc.add_paragraph()


def build_section_methodologie(doc: Document, ctx: dict) -> None:
    """Section méthodologie avec sous-sections et tableau IE couleurs."""
    doc.add_heading("Méthodologie", level=1)

    # 3.1 Visites terrain
    doc.add_heading("Visites terrains réalisés et moyens mis en œuvre", level=2)
    detail = ctx.get("detail_visite") or ""
    methods = ctx.get("investigation_methods") or ""
    for text in [detail, methods]:
        if text:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.add_run(text).font.size = Pt(9)
    if not detail and not methods:
        p = doc.add_paragraph()
        p.add_run("A remplir").font.size = Pt(9)
        p.runs[0].font.italic = True
        p.runs[0].font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)

    doc.add_paragraph()

    # 3.2 Indice d'état
    doc.add_heading("Indice d'état", level=2)

    intro = doc.add_paragraph()
    intro.paragraph_format.space_before = Pt(0)
    ir = intro.add_run(
        "Pour réaliser ce diagnostic structurel nous nous sommes inspirés de la méthode dite des "
        "Visites Simplifiées Comparées (méthode VSC), développée par le Cerema.\n"
        "Son application conduit à une connaissance globale du patrimoine permettant :"
    )
    ir.font.size = Pt(9)

    bullets = [
        "D'identifier et de traiter immédiatement les problèmes de sécurité : elle répond à ce "
        "titre au besoin des gestionnaires en lien avec leur responsabilité vis-à-vis des risques pénaux,",
        "D'établir une programmation pluriannuelle et hiérarchisée des actions de surveillance, "
        "d'entretien et de réparation.",
    ]
    for b in bullets:
        bp = doc.add_paragraph(style="List Bullet")
        bp.paragraph_format.space_before = Pt(0)
        bp.paragraph_format.space_after = Pt(2)
        br = bp.add_run(b)
        br.font.size = Pt(9)

    doc.add_paragraph()

    # IE color table
    _build_ie_table(doc)
    doc.add_paragraph()


def _build_ie_table(doc: Document) -> None:
    """Build the IE scale table with colored IE column."""
    # 6 columns: IE | Mécanique | Usages | Niveau | Type | Échéance
    tbl = doc.add_table(rows=1, cols=6)
    tbl.style = "Table Grid"
    set_table_borders(tbl, "888888")

    # Header row
    hdr = tbl.rows[0]
    hdr_texts = ["IE", "Évaluation — Mécanique", "Évaluation — Usages",
                 "Actions — Niveau", "Actions — Type", "Actions — Échéance"]
    for cell, h in zip(hdr.cells, hdr_texts):
        cell.text = h
        set_cell_shading(cell, IC_BLUE_HEX)
        if cell.paragraphs[0].runs:
            r = cell.paragraphs[0].runs[0]
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            r.font.bold = True
            r.font.size = Pt(8)
        set_cell_margins(cell, 40, 40, 60, 60)

    for ie_val, color_hex, mecanique, usages, niveau, type_action, echeance in IE_TABLE_ROWS:
        row = tbl.add_row()
        cells = row.cells
        values = [ie_val, mecanique, usages, niveau, type_action, echeance]
        for i, (cell, val) in enumerate(zip(cells, values)):
            cell.text = val
            if cell.paragraphs[0].runs:
                r = cell.paragraphs[0].runs[0]
                r.font.size = Pt(8)
                if i == 0:  # IE cell
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    set_cell_shading(cell, color_hex)
            set_cell_margins(cell, 40, 40, 60, 60)


# ── Section désordres (1 bloc / page par désordre) ────────────────────────────

def _labeled_block(doc: Document, label: str, text: str) -> None:
    if not text:
        return
    lp = doc.add_paragraph()
    lp.paragraph_format.space_before = Pt(6)
    lp.paragraph_format.space_after = Pt(0)
    lr = lp.add_run(label)
    lr.font.size = Pt(9)
    lr.font.bold = True
    lr.font.color.rgb = IC_BLUE
    tp = doc.add_paragraph()
    tp.paragraph_format.space_before = Pt(0)
    tp.paragraph_format.space_after = Pt(2)
    tp.paragraph_format.left_indent = Cm(0.5)
    tp.add_run(text).font.size = Pt(9)


def build_disorder_block(doc: Document, disorder: dict, photos_dir: str, is_first: bool) -> None:
    if not is_first:
        doc.add_page_break()

    ref = disorder.get("ref") or ""
    name = disorder.get("name") or disorder.get("desordre") or ""
    location = disorder.get("location") or disorder.get("localisation") or ""
    description = disorder.get("description") or disorder.get("observation") or ""
    cause = disorder.get("cause") or ""
    recommendations = disorder.get("recommendations") or disorder.get("action") or ""
    ie = disorder.get("ie")

    # Disorder header bar
    hdr_tbl = doc.add_table(rows=1, cols=1)
    hdr_cell = hdr_tbl.rows[0].cells[0]
    set_cell_shading(hdr_cell, IC_BLUE_HEX)
    set_cell_margins(hdr_cell, 80, 80, 120, 120)
    hdr_p = hdr_cell.paragraphs[0]
    if ref:
        rr = hdr_p.add_run(f"{ref}  ")
        rr.font.size = Pt(11)
        rr.font.bold = True
        rr.font.color.rgb = IC_ORANGE
    rn = hdr_p.add_run(name or "(sans titre)")
    rn.font.size = Pt(11)
    rn.font.bold = True
    rn.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    if location:
        lp = doc.add_paragraph()
        lp.paragraph_format.space_before = Pt(4)
        lp.paragraph_format.space_after = Pt(4)
        lr = lp.add_run(f"Localisation : {location}")
        lr.font.size = Pt(9)
        lr.font.italic = True
        lr.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # Photos (2-column table, max 4)
    photos = disorder.get("photos") or []
    if not photos and disorder.get("photo"):
        raw = disorder["photo"]
        photos = [{"path": raw, "caption": ref}] if raw else []

    resolved = []
    for ph in photos:
        path = ph.get("path") if isinstance(ph, dict) else str(ph)
        if path and not os.path.isabs(path):
            path = os.path.join(photos_dir, path)
        caption = ph.get("caption", "") if isinstance(ph, dict) else ""
        resolved.append({"path": path, "caption": caption})

    if resolved:
        capped = resolved[:4]
        pairs = [capped[i:i+2] for i in range(0, len(capped), 2)]
        if pairs and len(pairs[-1]) == 1:
            pairs[-1].append(None)

        photo_tbl = doc.add_table(rows=len(pairs), cols=2)
        set_table_borders(photo_tbl, "DDDDDD")
        for row_idx, pair in enumerate(pairs):
            row = photo_tbl.rows[row_idx]
            for col_idx, ph in enumerate(pair):
                cell = row.cells[col_idx]
                set_cell_margins(cell, 40, 40, 40, 40)
                if ph:
                    add_photo_to_cell(cell, ph["path"], max_width_cm=7.5)
                    if ph.get("caption"):
                        cap_p = cell.add_paragraph()
                        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        cap_r = cap_p.add_run(ph["caption"])
                        cap_r.font.size = Pt(7)
                        cap_r.font.italic = True
                        cap_r.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    # IE badge
    try:
        ie_val = int(ie)
    except (TypeError, ValueError):
        ie_val = None

    ie_tbl = doc.add_table(rows=1, cols=1)
    ie_cell = ie_tbl.rows[0].cells[0]
    set_cell_margins(ie_cell, 60, 60, 100, 100)
    if ie_val and ie_val in IE_COLORS:
        hex_color, label = IE_COLORS[ie_val]
        set_cell_shading(ie_cell, hex_color)
        dots = "■" * ie_val + "□" * (5 - ie_val)
        ie_r = ie_cell.paragraphs[0].add_run(f"  IE {ie_val}  {dots}  —  {label}  ")
        ie_r.font.size = Pt(10)
        ie_r.font.bold = True
        ie_r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    else:
        set_cell_shading(ie_cell, "EEEEEE")
        ie_r = ie_cell.paragraphs[0].add_run("  IE : non renseigné  ")
        ie_r.font.size = Pt(9)
        ie_r.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    _labeled_block(doc, "Description :", description)
    _labeled_block(doc, "Cause probable :", cause)
    _labeled_block(doc, "Recommandations :", recommendations)


def build_section_desordres(doc: Document, disorders: list, photos_dir: str) -> None:
    doc.add_heading("Désordres constatés", level=1)
    if not disorders:
        doc.add_paragraph().add_run("Aucun désordre enregistré.").font.italic = True
        doc.add_paragraph()
        return
    for i, disorder in enumerate(disorders):
        build_disorder_block(doc, disorder, photos_dir, is_first=(i == 0))


def build_section_synthese(doc: Document, ctx: dict) -> None:
    doc.add_page_break()
    doc.add_heading("Synthèse et conclusions", level=1)
    synthese = ctx.get("synthese") or ctx.get("observations") or ""
    conclusions = ctx.get("conclusions") or ctx.get("conclusion") or ""
    if synthese:
        p = doc.add_paragraph()
        p.add_run(synthese).font.size = Pt(9)
    if conclusions and conclusions != synthese:
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run(conclusions).font.size = Pt(9)
    doc.add_paragraph()


def build_section_recommandations(doc: Document, ctx: dict, disorders: list) -> None:
    doc.add_heading("Recommandations", level=1)
    global_reco = ctx.get("recommandations") or ""
    if global_reco:
        p = doc.add_paragraph()
        p.add_run(global_reco).font.size = Pt(9)
    elif disorders:
        for d in disorders:
            action = d.get("recommendations") or d.get("action") or ""
            ref = d.get("ref") or ""
            if not action:
                continue
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Cm(0.5)
            if ref:
                rr = p.add_run(f"[{ref}] ")
                rr.font.bold = True
                rr.font.size = Pt(9)
                rr.font.color.rgb = IC_BLUE
            p.add_run(action).font.size = Pt(9)
    doc.add_paragraph()


# ── Format normalization ───────────────────────────────────────────────────────

def _normalize_disorders(ctx: dict) -> list:
    if ctx.get("disorders"):
        return ctx["disorders"]
    disorders = []
    for obs in ctx.get("observations", []):
        photo_filenames = obs.get("photos") or ([obs.get("photo")] if obs.get("photo") else [])
        photos = [{"path": str(p), "caption": obs.get("ref", "")} for p in photo_filenames if p]
        disorders.append({
            "ref": obs.get("ref", ""),
            "name": obs.get("name") or obs.get("desordre", ""),
            "location": obs.get("localisation") or obs.get("zone", ""),
            "description": obs.get("observation") or obs.get("desordre", ""),
            "cause": "",
            "recommendations": obs.get("action", ""),
            "ie": obs.get("ie"),
            "photos": photos,
        })
    return disorders


# ── Main ──────────────────────────────────────────────────────────────────────

def render_diagnostic(context: dict, photos_dir: str = ".", output_path: str = "rapport_diagnostic.docx") -> str:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.0)

    setup_heading_styles(doc)
    disorders = _normalize_disorders(context)

    build_cover(doc, context)
    build_section_batiment(doc, context)
    build_section_contexte(doc, context)
    build_section_methodologie(doc, context)
    build_section_desordres(doc, disorders, photos_dir)
    build_section_synthese(doc, context)
    build_section_recommandations(doc, context, disorders)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)

    size_kb = out.stat().st_size / 1024
    print(f"✅ Rapport diagnostic : {out}")
    print(f"   {len(disorders)} désordre(s) | {size_kb:.0f} KB")
    return str(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rapport diagnostic IC Ingénieurs")
    parser.add_argument("context", help="context.json")
    parser.add_argument("--photos-dir", default=".", help="Dossier photos")
    parser.add_argument("--output", default="rapport_diagnostic.docx", help="Fichier de sortie")
    args = parser.parse_args()

    with open(args.context, encoding="utf-8") as f:
        ctx = json.load(f)

    render_diagnostic(ctx, args.photos_dir, args.output)
