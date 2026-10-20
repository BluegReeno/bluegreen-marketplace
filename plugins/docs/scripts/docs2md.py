#!/usr/bin/env python3
"""Turn a Claude Docs Word export into the Markdown that md2docx.py renders.

Usage:
    uv run --with python-docx --with pyyaml python3 scripts/docs2md.py export.docx -o doc.md

Why the Word export and not the Markdown export: the Word export keeps the table header row and
table cells holding several paragraphs, and leaves `{{?…}}` fields and markers unescaped.

Conventions written in the doc (see skills/brand/references/docs-authoring.md):
- a ```yaml code block holds the front matter; the doc's `# Title` is dropped when it repeats it;
- a paragraph `\\newpage` or `[[saut de page]]` is a page break;
- a paragraph `[[page Blue Green]]` (or `<!-- blue-green-page -->`) places the Blue Green page.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import yaml
    from docx import Document
    from docx.oxml.ns import qn
except ImportError as e:
    sys.exit(f"Missing dependency ({e.name}). Run with: uv run --with python-docx --with pyyaml python3 docs2md.py …")

MONTHS_EN = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
             "octobre", "novembre", "décembre"]


def find_pandoc():
    exe = shutil.which("pandoc")
    if exe:
        return exe
    try:
        import pypandoc
        return pypandoc.get_pandoc_path()
    except Exception:
        return None


def balance_columns(src, dst):
    """Docs exports equal column widths; weigh each column by its text instead.

    Returns one list of weights per top-level table, in document order: pandoc sizes the
    Markdown table by its content, so grid_to_pipe() applies these weights to the dashes.
    """
    doc = Document(src)
    all_weights = []
    for tbl in doc.tables:
        grid = tbl._tbl.find(qn("w:tblGrid"))
        if grid is None:
            continue
        cols = grid.findall(qn("w:gridCol"))
        chars = [0] * len(cols)
        word = [0] * len(cols)
        for row in tbl.rows:
            for i, cell in enumerate(row.cells[:len(cols)]):
                # a {{?…}} field renders as a ~20-character box, whatever its source length
                text = re.sub(r"\{\{\?[^}]*\}\}", "x" * 20, cell.text)
                chars[i] += len(text)
                word[i] = max([word[i]] + [len(w) for w in text.split()])
        # square root of the text volume, never narrower than the longest word
        weights = [max(c ** 0.5, w * 1.2, 3) for c, w in zip(chars, word)]
        if max(weights) < 1.5 * min(weights):  # near-even columns (signature blocks) → even
            weights = [1] * len(weights)
        all_weights.append(weights)
        total = sum(weights) or 1
        for col, w in zip(cols, weights):
            col.set(qn("w:w"), str(int(9000 * w / total)))
    doc.save(dst)
    return all_weights


def unescape(text):
    return re.sub(r"\\(.)", r"\1", text)


def french_dates(text):
    """Date chips export as 'Oct 15, 2026': write them the French way."""
    def repl(m):
        month = MONTHS_EN.index(m.group(1)[:3].lower())
        return f"{int(m.group(2))} {MONTHS_FR[month]} {m.group(3)}"
    return re.sub(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? (\d{1,2}), (\d{4})\b", repl, text)


KEY_LINE = re.compile(r"^[A-Za-z_]+:(\s|$)")


def front_matter(md):
    """Lift the doc's yaml code block out of the body; it becomes the front matter.

    The Word export turns a code block into a plain paragraph whose lines end with a hard break,
    so the block is found by its shape: the first paragraph among the first few made only of
    `key: value` lines.
    """
    blocks = md.split("\n\n")
    for i, block in enumerate(blocks[:6]):
        text = block.strip().strip("`").replace("yaml\n", "", 1) if block.strip().startswith("```") else block
        lines = [unescape(l.rstrip().rstrip("\\")) for l in text.strip().split("\n")]
        if lines and all(KEY_LINE.match(l) for l in lines if l.strip()):
            try:
                meta = yaml.safe_load("\n".join(lines))
            except yaml.YAMLError:
                continue
            if isinstance(meta, dict):
                return meta, "\n\n".join(blocks[:i] + blocks[i + 1:])
    return {}, md


def tighten_lists(md):
    """Word export items come back as loose lists; keep them tight like hand-written Markdown."""
    return re.sub(r"^((?:-|\d+\.)\s+.+)\n\n(?=(?:-|\d+\.)\s)", r"\1\n", md, flags=re.M)


def drop_title(md, meta):
    """The doc's leading `# Title` repeats the front matter title (or provides it)."""
    m = re.search(r"^# (.+?)\s*(\{[^}]*\})?\s*$", md, re.M)
    if not m or md[:m.start()].strip():
        return md
    heading = unescape(m.group(1)).strip()
    if not meta.get("title"):
        meta["title"] = heading
    elif heading != str(meta["title"]).strip():
        return md
    return md[:m.start()] + md[m.end():]


MARKERS = {
    r"\newpage": r"\newpage",
    r"\pagebreak": r"\newpage",
    "[[saut de page]]": r"\newpage",
    "<!-- blue-green-page -->": "<!-- blue-green-page -->",
    "[[page blue green]]": "<!-- blue-green-page -->",
}


def restore_markers(md):
    out = []
    for line in md.split("\n"):
        bare = line.strip().replace("\\", "").lower()
        hit = next((v for k, v in MARKERS.items() if bare == k.replace("\\", "")), None)
        out.append(hit if hit else line)
    return "\n".join(out)


GRID_RULE = re.compile(r"^\+[-=+:]+\+$")


def regrid(block, weights):
    """Widen a grid table's columns to the given proportions (pandoc sizes them by content).

    A grid column can be wider than its text but never narrower, so every column is scaled by
    the one factor that fits the most crowded column.
    """
    cuts = [n for n, ch in enumerate(block[0]) if ch == "+"]
    if not weights or len(weights) != len(cuts) - 1:
        return block
    spans = list(zip(cuts, cuts[1:]))
    content = [b - a - 1 for a, b in spans]
    scale = max(c / w for c, w in zip(content, weights))
    target = [max(c, round(w * scale)) for c, w in zip(content, weights)]
    out = []
    for line in block:
        sep = "+" if GRID_RULE.match(line) else "|"
        segs = []
        for (a, b), t in zip(spans, target):
            seg = line[a + 1:b]
            fill = seg[-1] if sep == "+" and seg else " "
            segs.append(seg + fill * (t - len(seg)))
        out.append(sep + sep.join(segs) + sep)
    return out


def grid_to_pipe(md, table_weights=()):
    """Rewrite grid tables whose rows are all one line as pipe tables.

    md2docx expands `{{?…}}` fields before pandoc reads the table, which breaks a grid table's
    column alignment; pipe tables do not care. Only tables with multi-paragraph cells stay grid.
    """
    lines, out, i, k = md.split("\n"), [], 0, 0
    while i < len(lines):
        if not GRID_RULE.match(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        j = i
        while j + 1 < len(lines) and (GRID_RULE.match(lines[j + 1]) or lines[j + 1].startswith("|")):
            j += 1
        block = lines[i:j + 1]
        weights = table_weights[k] if k < len(table_weights) else None
        k += 1
        rows, rules = [l for l in block if l.startswith("|")], [l for l in block if GRID_RULE.match(l)]
        if len(rules) != len(rows) + 1:  # a row spans several lines: keep the grid table
            out.extend(regrid(block, weights))
        else:
            widths = [len(seg) for seg in rules[0].strip("+").split("+")]
            if weights and len(weights) == len(widths):
                widths = [60 * w / sum(weights) for w in weights]
            dashes = "|" + "|".join("-" * max(3, round(w)) for w in widths) + "|"
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            header = any("=" in r for r in rules)
            head = cells[0] if header else [""] * len(widths)
            body = cells[1:] if header else cells
            out.append("| " + " | ".join(head) + " |")
            out.append(dashes)
            out.extend("| " + " | ".join(c) + " |" for c in body)
        i = j + 1
    return "\n".join(out)


TEXT_WIDTH_IN = 6.5  # A4 minus md2docx margins (2 × 2.2 cm)


def relative_images(md):
    """Word export sizes images in inches; the brand renderer takes a share of the text width."""
    def repl(m):
        pct = min(100, round(float(m.group(1)) / TEXT_WIDTH_IN * 100))
        return "{width=" + str(pct) + "%}"
    return re.sub(r'\{width="([\d.]+)in"(?: height="[\d.]+in")?\}', repl, md)


def clean(md, meta, table_weights=()):
    md = grid_to_pipe(md, table_weights)
    md = relative_images(md)
    md = restore_markers(md)
    for _ in range(2):  # overlapping matches need a second pass
        md = tighten_lists(md)
    md = re.sub(r"\{\{(.*?)\}\}", lambda m: "{{" + unescape(m.group(1)) + "}}", md)  # {{?Label#name_x}}
    md = french_dates(md)
    md = re.sub(r"\\@(\w)", r"\1", md)  # mention chips: keep the name, drop the @
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    head = "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip() + "\n---\n\n"
    return head + md


def warnings(md):
    notes = []
    if re.search(r"^\|", md, re.M) and "|---" not in md.replace(" ", "") and "+===" not in md:
        notes.append("a table has no header row")
    if "[[" in md or "]]" in md:
        notes.append("a [[…]] marker was not recognised")
    if re.search(r"<(span|div|br)\b", md):
        notes.append("raw HTML left in the Markdown (lost in Word)")
    return notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="the .docx exported from Claude Docs")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    pandoc = find_pandoc()
    if not pandoc:
        sys.exit("pandoc not found. Install it, or add `--with pypandoc_binary` to the uv command.")
    src = os.path.abspath(args.source)
    out = os.path.abspath(args.output or os.path.splitext(src)[0] + ".md")
    media = os.path.join(os.path.dirname(out), os.path.splitext(os.path.basename(out))[0] + "_media")

    with tempfile.TemporaryDirectory() as tmp:
        balanced = os.path.join(tmp, "balanced.docx")
        table_weights = balance_columns(src, balanced)
        md = subprocess.run(
            [pandoc, balanced, "-t", "markdown-smart-simple_tables-multiline_tables-raw_html-native_divs-native_spans",
             "--wrap=none", f"--extract-media={media}"],
            check=True, capture_output=True, text=True).stdout

    meta, md = front_matter(md)
    md = drop_title(md, meta)
    meta.setdefault("type", "document")
    md = clean(md, meta, table_weights)
    md = md.replace(media + "/", os.path.basename(media) + "/")  # image paths relative to the .md
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(out)
    for n in warnings(md):
        print("warning:", n, file=sys.stderr)


if __name__ == "__main__":
    main()
