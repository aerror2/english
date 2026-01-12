#!/usr/bin/env python3
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
    ap = argparse.ArgumentParser(description="Convert PDF(s) to TXT using pypdf.")
    ap.add_argument("inputs", nargs="+", help="PDF file(s) or directory(ies).")
    ap.add_argument(
        "-o",
        "--out-dir",
        default="pdf_txt",
        help="Output directory (default: ./pdf_txt)",
    )
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing TXT files.")
    args = ap.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pdfs: list[Path] = []
    for inp in args.inputs:
        p = Path(inp).expanduser()
        if p.is_dir():
            pdfs.extend(sorted(p.rglob("*.pdf")))
        else:
            pdfs.append(p)

    pdfs = [p.resolve() for p in pdfs if p.exists() and p.suffix.lower() == ".pdf"]
    if not pdfs:
        print("No PDFs found.")
        return 2

    converted = 0
    for pdf in pdfs:
        out_path = out_dir / (pdf.stem + ".txt")
        if out_path.exists() and not args.overwrite:
            continue
        try:
            text = pdf_to_text(pdf)
            out_path.write_text(text, encoding="utf-8")
            converted += 1
        except Exception as e:
            print(f"[FAIL] {pdf}: {e}")

    print(f"Done. Converted {converted}/{len(pdfs)} PDF(s) into: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

