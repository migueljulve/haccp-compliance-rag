"""Parse the HACCP source corpus into a common list-of-chunks format."""

import xml.etree.ElementTree as ET

import re
import xml.etree.ElementTree as ET
from pypdf import PdfReader


#XMLs

def split_long(paragraphs: list[str], max_chars: int = 1500) -> list[list[str]]:
    groups = []
    current, current_len = [], 0
    for p in paragraphs:
        if current and current_len + len(p) > max_chars:
            groups.append(current)
            current, current_len = [], 0
        current.append(p)
        current_len += len(p)
    if current:
        groups.append(current)
    return groups



def parse_ecfr(path: str, source: str) -> list[dict]:
    root = ET.parse(path).getroot()
    chunks = []

    for section in root.findall(".//DIV8[@TYPE='SECTION']"):
        number = section.attrib["N"]

        head = "".join(section.find("HEAD").itertext()).strip()
        title = head.split(number, 1)[-1].strip().rstrip(".")

        paragraphs = [
            " ".join("".join(p.itertext()).split()) for p in section.findall("P")
        ]
        groups = split_long(paragraphs)
        for i, group in enumerate(groups):
            body = "\n\n".join(group)
            part = f" (part {i + 1}/{len(groups)})" if len(groups) > 1 else ""
            chunks.append(
                {
                    "source": source,
                    "section": number,
                    "title": title,
                    "citation": f"{source} § {number}",
                    "page": None,
                    "text": f"{title}{part}\n\n{body}",
                }
            )

        

    return chunks

#PDF CODEX

CODEX_HEADER_LINE = "CODE OF PRACTICE CXC 1-1969 GENERAL PRINCIPLES OF FOOD HYGIENE"
CODEX_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*\.?)\s+(\S.*)$")
CODEX_BODY_PAGES = range(6, 54)


def parse_codex(path: str, source: str = "Codex CXC 1-1969") -> list[dict]:
    reader = PdfReader(path)
    lines = []
    for page_num in CODEX_BODY_PAGES:
        text = reader.pages[page_num].extract_text() or ""
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line or line.isdigit() or line == CODEX_HEADER_LINE:
                continue
            line = re.sub(r"^(\d+)\s+\.", r"\1.", line)
            lines.append(line)

    sections = []
    for line in lines:
        m = CODEX_HEADING_RE.match(line)
        if m and "." in m.group(1):
            sections.append(
                {"number": m.group(1).rstrip("."), "title": m.group(2).strip(), "lines": []}
            )
        elif sections:
            sections[-1]["lines"].append(line)

    chunks = []
    for sec in sections:
        groups = split_long(sec["lines"])
        for i, group in enumerate(groups):
            body = " ".join(group)
            part = f" (part {i + 1}/{len(groups)})" if len(groups) > 1 else ""
            chunks.append(
                {
                    "source": source,
                    "section": sec["number"],
                    "title": sec["title"],
                    "citation": f"{source} § {sec['number']}",
                    "page": None,
                    "text": f"{sec['title']}{part}\n\n{body}",
                }
            )

    return chunks

#PDF fsis

FSIS_STEP_RE = re.compile(r"^(STEP\s+\d+)\s*[-–—]\s*(.*)$")
FSIS_PRINCIPLE_RE = re.compile(r"^(STEPS IN .+)$")
FSIS_BODY_PAGES = range(3, 29)


def parse_fsis(path: str, source: str = "FSIS HACCP Guidebook") -> list[dict]:
    reader = PdfReader(path)
    lines = []
    for page_num in FSIS_BODY_PAGES:
        text = reader.pages[page_num].extract_text() or ""
        for raw_line in text.split("\n"):
            line = re.sub(r"/c\d+", "", raw_line)
            line = re.sub(r"^C-\d+\s*", "", line)
            line = line.strip()
            if line:
                lines.append(line)

    sections = []
    for line in lines:
        m_step = FSIS_STEP_RE.match(line)
        m_principle = FSIS_PRINCIPLE_RE.match(line)
        if m_step:
            sections.append(
                {"number": m_step.group(1), "title": m_step.group(2).strip(), "lines": []}
            )
        elif m_principle:
            sections.append(
                {"number": m_principle.group(1), "title": m_principle.group(1), "lines": []}
            )
        elif sections:
            sections[-1]["lines"].append(line)

    chunks = []
    for sec in sections:
        groups = split_long(sec["lines"])
        for i, group in enumerate(groups):
            body = " ".join(group)
            part = f" (part {i + 1}/{len(groups)})" if len(groups) > 1 else ""
            chunks.append(
                {
                    "source": source,
                    "section": sec["number"],
                    "title": sec["title"],
                    "citation": f"{source}, {sec['number']}",
                    "page": None,
                    "text": f"{sec['title']}{part}\n\n{body}",
                }
            )

    return chunks

#TOTAL
def parse_all() -> list[dict]:
    chunks = []
    chunks += parse_ecfr("data/raw/ecfr_21cfr123_2026-08-01.xml", "21 CFR 123")
    chunks += parse_ecfr("data/raw/ecfr_21cfr120_2026-08-01.xml", "21 CFR 120")
    chunks += parse_codex("data/raw/codex_cxc_1-1969.pdf")
    chunks += parse_fsis("data/raw/fsis_haccp_guidebook.pdf")
    return chunks



if __name__ == "__main__":

    # XML
    sources = [
        ("data/raw/ecfr_21cfr123_2026-08-01.xml", "21 CFR 123"),
        ("data/raw/ecfr_21cfr120_2026-08-01.xml", "21 CFR 120"),
    ]

    for path, source in sources:
        chunks = parse_ecfr(path, source)
        sizes = [len(c["text"]) for c in chunks]
        print(f"\n{source}: {len(chunks)} chunks, "
              f"min {min(sizes)} / max {max(sizes)} chars")
        for c in chunks[:3]:
            print(f"  {c['citation']:<16} | {c['title'][:50]}")

    #pdf codex
    codex_chunks = parse_codex("data/raw/codex_cxc_1-1969.pdf")
    sizes = [len(c["text"]) for c in codex_chunks]
    print(f"\nCodex CXC 1-1969: {len(codex_chunks)} chunks, "
          f"min {min(sizes)} / max {max(sizes)} chars")
    for c in codex_chunks[:8]:
        print(f"  {c['citation']:<22} | {c['title'][:50]}")

    #pdf fsis
    fsis_chunks = parse_fsis("data/raw/fsis_haccp_guidebook.pdf")
    sizes = [len(c["text"]) for c in fsis_chunks]
    print(f"\nFSIS HACCP Guidebook: {len(fsis_chunks)} chunks, "
          f"min {min(sizes)} / max {max(sizes)} chars")
    for c in fsis_chunks[:12]:
        print(f"  {c['section']:<40} | {c['title'][:40]}")



    #print TOTAL
    print(f"\nTOTAL: {len(parse_all())} chunks across all sources")
