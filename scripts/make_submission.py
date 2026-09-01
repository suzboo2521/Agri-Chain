"""Assemble the AgriChain submission bundle → AgriChain_submission.zip.

Bundles the documentation directory (installation guide, how-it-works, API,
security, end-to-end test results, architecture diagram), the top-level README,
and the judge presentation.

Run:  python -m scripts.make_submission
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DOCS_DIR, PRESENTATION_DIR, ROOT  # noqa: E402

ZIP_PATH = ROOT / "AgriChain_submission.zip"
DECK = PRESENTATION_DIR / "AgriChain.pptx"


def _collect() -> list[Path]:
    items: list[Path] = []
    readme = ROOT / "README.md"
    if readme.exists():
        items.append(readme)
    # entire docs/ directory (md + architecture.png + test results)
    if DOCS_DIR.exists():
        items.extend(sorted(p for p in DOCS_DIR.rglob("*") if p.is_file()))
    if DECK.exists():
        items.append(DECK)
    return items


def main() -> int:
    files = _collect()
    missing = [name for name, p in (("README.md", ROOT / "README.md"),
                                    ("presentation/AgriChain.pptx", DECK)) if not p.exists()]
    if missing:
        print(f"⚠ warning: missing expected artifacts: {', '.join(missing)}")

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            arcname = f.relative_to(ROOT)
            zf.write(f, arcname)

    size_kb = ZIP_PATH.stat().st_size / 1024
    print(f"Wrote {ZIP_PATH}  ({size_kb:.1f} KB)")
    print(f"Contents ({len(files)} files):")
    for f in files:
        print(f"  - {f.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
