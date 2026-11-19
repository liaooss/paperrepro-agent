"""Paper ingest: LaTeX, Markdown, HTML and (optionally) PDF.

The goal is not to render a paper but to recover two things the audit needs:
named sections (so claims can cite "Section 4.2") and tables with their header
row intact (so numbers keep their column meaning).
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path

from ..models import PaperDoc, PaperTable

__all__ = ["load_paper"]


class IngestError(RuntimeError):
    """Raised when a paper cannot be read at all."""


# --------------------------------------------------------------------------- #
# LaTeX
# --------------------------------------------------------------------------- #

_TEX_SECTION = re.compile(r"\\(section|subsection|subsubsection)\*?\s*\{")
_TEX_COMMENT = re.compile(r"(?<!\\)%.*")
_TEX_FORMAT_CMDS = (
    "textbf",
    "textit",
    "emph",
    "texttt",
    "textsc",
    "textrm",
    "text",
    "mathrm",
    "mathbf",
    "mathit",
    "underline",
    "MakeUppercase",
)


def _read_group(src: str, i: int) -> tuple[str, int]:
    """Read a ``{...}`` group starting at ``i`` and return (content, index after)."""
    if i >= len(src) or src[i] != "{":
        return "", i
    depth = 0
    start = i + 1
    j = i
    while j < len(src):
        ch = src[j]
        if ch == "\\":
            j += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start:j], j + 1
        j += 1
    return src[start:], len(src)


def _strip_tex_commands(text: str) -> str:
    """Reduce LaTeX markup to readable prose, best effort."""
    out = _TEX_COMMENT.sub("", text)
    # Keep the argument of formatting commands, drop the command itself.
    for cmd in _TEX_FORMAT_CMDS:
        pattern = re.compile(r"\\" + cmd + r"\s*\{")
        guard = 0
        while guard < 200:
            m = pattern.search(out)
            if not m:
                break
            inner, after = _read_group(out, m.end() - 1)
            out = out[: m.start()] + inner + out[after:]
            guard += 1
    # Commands that carry no prose.
    out = re.sub(r"\\(cite|citep|citet|ref|eqref|label|footnote|thanks)\*?(\[[^\]]*\])?\{[^{}]*\}", "", out)
    out = re.sub(r"\\(begin|end)\{[^{}]*\}", " ", out)
    out = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", out)
    out = out.replace("\\\\", " ").replace("~", " ")
    out = out.replace("{", "").replace("}", "")
    out = out.replace("$", "")
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _clean_cell(cell: str) -> str:
    text = cell.strip()
    text = re.sub(r"\\(hline|toprule|midrule|bottomrule|cmidrule)(\([^)]*\))?(\{[^{}]*\})?", "", text)
    # \multicolumn{n}{spec}{content} -> content
    for _ in range(4):
        m = re.search(r"\\multicolumn\s*\{[^{}]*\}\s*\{[^{}]*\}\s*\{", text)
        if not m:
            break
        inner, after = _read_group(text, m.end() - 1)
        text = text[: m.start()] + inner + text[after:]
    text = _strip_tex_commands(text)
    text = text.replace("\u2212", "-").strip()
    return re.sub(r"\s+", " ", text)


def _split_tex_rows(body: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw in re.split(r"\\\\(?:\[[^\]]*\])?", body):
        raw = raw.strip()
        if not raw:
            continue
        # Drop stray rule commands that survived on their own line.
        raw = re.sub(r"\\(hline|toprule|midrule|bottomrule|addlinespace)(\[[^\]]*\])?", "", raw).strip()
        if not raw:
            continue
        cells = [_clean_cell(c) for c in raw.split("&")]
        if any(cells):
            rows.append(cells)
    return rows


def _table_id(index: int) -> str:
    return f"Table {index}"


def _parse_tex_tables(src: str, section_at: list[tuple[int, str]]) -> list[PaperTable]:
    tables: list[PaperTable] = []
    for env in ("table", "table*", "longtable", "tablex"):
        pattern = re.compile(r"\\begin\{" + re.escape(env) + r"\}")
        for m in pattern.finditer(src):
            end_marker = "\\end{" + env + "}"
            end = src.find(end_marker, m.end())
            if end == -1:
                continue
            block = src[m.start() : end]
            caption = ""
            cap_m = re.search(r"\\caption\*?\s*\{", block)
            if cap_m:
                caption = _strip_tex_commands(_read_group(block, cap_m.end() - 1)[0])
            body = ""
            for tab_env in ("tabular*", "tabular", "tabularx", "longtable"):
                tm = re.search(r"\\begin\{" + re.escape(tab_env) + r"\}", block)
                if tm:
                    tend = block.find("\\end{" + tab_env + "}", tm.end())
                    start = tm.end()
                    # Skip the column specification: [pos]{lcc}
                    spec = re.match(r"\s*(\[[^\]]*\])?\s*(\{[^{}]*\})?", block[start:])
                    if spec:
                        start += spec.end()
                    body = block[start : tend if tend != -1 else len(block)]
                    break
            if not body:
                continue
            rows = _split_tex_rows(body)
            if not rows:
                continue
            header = rows[0]
            data = rows[1:]
            if not data:
                continue
            section = ""
            for pos, name in section_at:
                if pos < m.start():
                    section = name
                else:
                    break
            tables.append(
                PaperTable(
                    id=_table_id(len(tables) + 1),
                    caption=caption,
                    header=header,
                    rows=data,
                    section=section,
                )
            )
    return tables


def _parse_tex(src: str, path: str) -> PaperDoc:
    src = src.replace("\r\n", "\n")
    title = ""
    m = re.search(r"\\title\s*\{", src)
    if m:
        title = _strip_tex_commands(_read_group(src, m.end() - 1)[0])

    headings: list[tuple[int, str, str]] = []  # (offset, name, heading text)
    for m in _TEX_SECTION.finditer(src):
        name, after = _read_group(src, m.end() - 1)
        headings.append((m.start(), m.group(1), _strip_tex_commands(name)))

    sections: dict[str, str] = {}
    for idx, (start, _level, name) in enumerate(headings):
        body_start = src.find("}", start)
        body_end = headings[idx + 1][0] if idx + 1 < len(headings) else len(src)
        body = _strip_tex_commands(src[body_start:body_end])
        if name:
            sections[name] = body

    abs_m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.DOTALL)
    if abs_m:
        sections.setdefault("Abstract", _strip_tex_commands(abs_m.group(1)))

    section_at = [(start, name) for start, _level, name in headings]
    tables = _parse_tex_tables(src, section_at)

    body_text = _strip_tex_commands(re.sub(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", " ", src, flags=re.DOTALL))
    return PaperDoc(
        path=path,
        format="tex",
        title=title,
        sections=sections,
        tables=tables,
        text=body_text,
    )


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #

_MD_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_MD_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")


def _parse_md_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip().strip("`*_") for c in line.split("|")]


def _parse_markdown(src: str, path: str) -> PaperDoc:
    lines = src.replace("\r\n", "\n").split("\n")
    title = ""
    sections: dict[str, str] = {}
    tables: list[PaperTable] = []
    heading = ""
    buf: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        hm = _MD_HEADING.match(line)
        if hm:
            if heading:
                sections[heading] = "\n".join(buf).strip()
            elif "".join(buf).strip():
                sections.setdefault("Preamble", "\n".join(buf).strip())
            heading = hm.group(2).strip()
            if not title and len(hm.group(1)) == 1:
                title = heading
            buf = []
            i += 1
            continue
        # Pipe table: header row followed by a separator row.
        if (
            "|" in line
            and i + 1 < len(lines)
            and _MD_TABLE_SEP.match(lines[i + 1])
        ):
            header = _parse_md_row(line)
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and "|" in lines[j] and lines[j].strip():
                cells = _parse_md_row(lines[j])
                if any(cells):
                    rows.append(cells)
                j += 1
            if rows:
                tables.append(
                    PaperTable(
                        id=_table_id(len(tables) + 1),
                        caption="",
                        header=header,
                        rows=rows,
                        section=heading,
                    )
                )
            i = j
            continue
        buf.append(line)
        i += 1
    if heading:
        sections[heading] = "\n".join(buf).strip()
    elif "".join(buf).strip():
        sections.setdefault("Preamble", "\n".join(buf).strip())

    body = "\n".join(f"{h}\n{t}" for h, t in sections.items())
    return PaperDoc(
        path=path, format="markdown", title=title, sections=sections, tables=tables, text=body
    )


# --------------------------------------------------------------------------- #
# HTML (ar5iv / arxiv abstract pages)
# --------------------------------------------------------------------------- #


class _PaperHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sections: dict[str, str] = {}
        self.tables: list[PaperTable] = []
        self.title = ""
        self._heading = ""
        self._buf: list[str] = []
        self._in_heading = False
        self._heading_tag = ""
        self._in_title = False
        self._table: PaperTable | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._caption: list[str] | None = None

    # -- helpers ---------------------------------------------------------- #
    def _flush(self) -> None:
        text = re.sub(r"\s+", " ", " ".join(self._buf)).strip()
        self._buf = []
        if not text:
            return
        if self._heading:
            existing = self.sections.get(self._heading, "")
            self.sections[self._heading] = (existing + " " + text).strip() if existing else text
        else:
            self.sections.setdefault("Preamble", "")
            existing = self.sections["Preamble"]
            self.sections["Preamble"] = (existing + " " + text).strip() if existing else text

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush()
            self._in_heading = True
            self._heading_tag = tag
            self._buf = []
            return
        if tag == "title":
            self._in_title = True
            return
        if tag == "table":
            self._flush()
            self._table = PaperTable(id=_table_id(len(self.tables) + 1), section=self._heading)
            return
        if tag == "caption" and self._table is not None:
            self._caption = []
            return
        if tag == "tr" and self._table is not None:
            self._row = []
            return
        if tag in {"td", "th"} and self._table is not None:
            self._cell = []
            return

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._in_heading:
            text = re.sub(r"\s+", " ", " ".join(self._buf)).strip()
            self._buf = []
            if tag == "h1" and not self.title:
                self.title = text
            self._heading = text
            # Register the heading even when it has no prose, so a table under
            # it keeps its section reference.
            if text:
                self.sections.setdefault(text, "")
            self._in_heading = False
            return
        if tag == "title":
            self._in_title = False
            return
        if tag in {"p", "li", "div", "section", "article"}:
            self._flush()
            return
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(re.sub(r"\s+", " ", " ".join(self._cell)).strip())
            self._cell = None
            return
        if tag == "caption" and self._caption is not None and self._table is not None:
            self._table.caption = re.sub(r"\s+", " ", " ".join(self._caption)).strip()
            self._caption = None
            return
        if tag == "tr" and self._row is not None and self._table is not None:
            if any(self._row):
                self._table.rows.append(self._row)
            self._row = None
            return
        if tag == "table" and self._table is not None:
            if self._table.rows:
                if len(self._table.rows) == 1:
                    self._table.header = self._table.rows[0]
                    self._table.rows = []
                else:
                    self._table.header = self._table.rows[0]
                    self._table.rows = self._table.rows[1:]
                if self._table.rows:
                    self.tables.append(self._table)
            self._table = None
            return

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
            return
        if self._cell is not None:
            self._cell.append(data)
            return
        if self._caption is not None:
            self._caption.append(data)
            return
        if self._table is not None:
            return
        self._buf.append(data)


def _parse_html(src: str, path: str) -> PaperDoc:
    parser = _PaperHTMLParser()
    parser.feed(src)
    parser._flush()
    sections = dict(parser.sections)
    body = "\n".join(f"{h}\n{t}" for h, t in sections.items())
    return PaperDoc(
        path=path,
        format="html",
        title=html.unescape(parser.title).strip(),
        sections=sections,
        tables=parser.tables,
        text=body,
    )


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #


def _parse_pdf(path: str) -> PaperDoc:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise IngestError(
            "PDF input needs the 'pdf' extra: pip install 'paperrepro[pdf]'. "
            "LaTeX, Markdown and HTML sources need no extra dependency."
        ) from exc
    try:
        reader = PdfReader(path)
    except Exception as exc:  # pragma: no cover - library specific
        raise IngestError(f"Could not read PDF {path}: {exc}") from exc
    chunks: list[str] = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    text = "\n".join(chunks)
    # Headings are unrecoverable from text, so expose the whole body as one section.
    sections = {"Body": text} if text.strip() else {}
    return PaperDoc(
        path=path,
        format="pdf",
        title=Path(path).stem,
        sections=sections,
        tables=[],
        text=text,
        warnings=["PDF input: tables are not parsed; pass the LaTeX source for table-level claims."],
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def load_paper(path: str | Path) -> PaperDoc:
    """Load a paper from disk and normalise it into a :class:`PaperDoc`."""
    p = Path(path)
    if not p.exists():
        raise IngestError(f"Paper not found: {p}")
    suffix = p.suffix.lower()
    raw = p.read_bytes()
    if suffix == ".pdf":
        return _parse_pdf(str(p))

    text = raw.decode("utf-8", errors="replace")
    if suffix in {".tex", ".latex"}:
        doc = _parse_tex(text, str(p))
    elif suffix in {".md", ".markdown", ".mdown"}:
        doc = _parse_markdown(text, str(p))
    elif suffix in {".html", ".htm", ".xhtml"}:
        doc = _parse_html(text, str(p))
    elif suffix in {".txt", ".rst"}:
        sections = {"Body": text}
        doc = PaperDoc(path=str(p), format="text", title=p.stem, sections=sections, text=text)
    else:
        # Last resort: sniff the content.
        if "\\documentclass" in text or "\\section{" in text:
            doc = _parse_tex(text, str(p))
        elif "<html" in text[:2000].lower():
            doc = _parse_html(text, str(p))
        elif re.search(r"^#{1,3}\s+", text, re.MULTILINE):
            doc = _parse_markdown(text, str(p))
        else:
            doc = PaperDoc(
                path=str(p),
                format="text",
                title=p.stem,
                sections={"Body": text},
                text=text,
                warnings=["Unknown paper format; treated as plain text."],
            )
    if not doc.sections and not doc.text:
        raise IngestError(f"No readable text found in {p}")
    return doc
