"""Keep docs/supported_instruments.md honest.

Every driver named in a docs table must exist as a class under
``instrumation.drivers``, and the Summary table must match the rows above
it. Catches the drift that let a removed driver (and a stale total) sit in
the docs after the code changed.
"""

import ast
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "supported_instruments.md"
DRIVERS_DIR = ROOT / "src" / "instrumation" / "drivers"

TABLE_ROW = re.compile(r"^\|\s*`([A-Za-z_][A-Za-z0-9_]*)`\s*\|")
CATEGORY = re.compile(r"^##\s+(.+)$")
SUMMARY_ROW = re.compile(r"^\|\s*([^|*]+?)\s*\|\s*(\d+)\s*\|")
SUMMARY_TOTAL = re.compile(r"^\|\s*\*\*Total\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|", re.M)


def _driver_classes():
    """Class names defined anywhere under instrumation/drivers."""
    found = set()
    for path in DRIVERS_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        found.update(n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    return found


def _doc_sections():
    """Ordered (category, [driver names]) parsed from the docs tables."""
    sections, category = [], None
    for line in DOC.read_text(encoding="utf-8", errors="replace").splitlines():
        heading = CATEGORY.match(line)
        if heading:
            category = heading.group(1).strip()
            sections.append((category, []))
            continue
        row = TABLE_ROW.match(line)
        if row and category:
            sections[-1][1].append(row.group(1))
    return sections


def test_every_documented_driver_exists():
    classes = _driver_classes()
    missing = [
        f"{name} (in section '{category}')"
        for category, names in _doc_sections()
        for name in names
        if name not in classes
    ]
    assert not missing, "docs name drivers that do not exist: " + ", ".join(missing)


def test_summary_counts_match_sections():
    text = DOC.read_text(encoding="utf-8", errors="replace")
    summary_block = text.split("## Summary", 1)[1]
    documented = {category: len(names) for category, names in _doc_sections()}
    # GENERIC is a fallback key, not an instrument category in the summary.
    documented.pop("GENERIC (Universal Fallback)", None)

    mismatches = []
    for line in summary_block.splitlines():
        row = SUMMARY_ROW.match(line)
        if not row:
            continue
        category, claimed = row.group(1).strip().lstrip("*").strip(), int(row.group(2))
        if category.lower().startswith("total") or category not in documented:
            continue
        if documented[category] != claimed:
            mismatches.append(f"{category}: docs say {claimed}, tables list {documented[category]}")
    assert not mismatches, "summary counts drifted: " + "; ".join(mismatches)

    total = SUMMARY_TOTAL.search(summary_block)
    assert total, "Summary has no **Total** row"
    assert int(total.group(1)) == sum(documented.values()), (
        f"summary total says {total.group(1)}, tables list {sum(documented.values())}"
    )
