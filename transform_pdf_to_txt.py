#!/usr/bin/env python3
"""
Convert all PDFs in a directory to TXT files.
Output directory: pdftxt/ (default: next to this script, or use -d).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader


def pdf_to_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            t = page.extract_text() or ""
        except Exception as e:
            t = f"\n[ERROR extracting page {i + 1}: {e}]\n"
        parts.append(t)
    return "\n\n".join(parts).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Transform all PDFs to TXT; output in pdftxt/.")
    ap.add_argument(
        "input_dir",
        nargs="?",
        default=".",
        help="Directory to scan for PDFs (default: current directory).",
    )
    ap.add_argument(
        "-o", "--out-dir",
        default="pdftxt",
        help="Output directory (default: pdftxt).",
    )
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing TXT files.")
    args = ap.parse_args()

    base = Path(args.input_dir).expanduser().resolve()
    if not base.is_dir():
        print(f"Not a directory: {base}")
        return 2

    out_dir = Path(args.out_dir).expanduser().resolve()
    if out_dir != base:
        out_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(base.rglob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found under: {base}")
        return 0

    converted = 0
    for pdf in pdfs:
        out_path = out_dir / (pdf.stem + ".txt")
        if out_path.exists() and not args.overwrite:
            continue
        try:
            text = pdf_to_text(pdf)
            out_path.write_text(text, encoding="utf-8")
            converted += 1
            print(f"  {pdf.name} -> {out_path.name}")
        except Exception as e:
            print(f"[FAIL] {pdf.name}: {e}")

    print(f"Done. Converted {converted}/{len(pdfs)} PDF(s) into: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
