#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha1

from pypdf import PdfReader


def _short_id(s: str) -> str:
    return sha1(s.encode("utf-8")).hexdigest()[:12]

def _normalize_text(text: str) -> str:
    # PDFs often have hard newlines; normalize into spaces and collapse whitespace.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    """
    Heuristic sentence splitting for extracted PDF text.
    Keeps it simple: split on . ! ? followed by whitespace.
    """
    if not text:
        return []
    # Ensure spacing is normalized so the split is stable.
    text = _normalize_text(text)
    # Split after punctuation marks.
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p and p.strip()]


def _snippets_from_text(
    rx: re.Pattern,
    text: str,
    sentences: int = 1,
    max_snippets: int = 3,
    snippet_max_chars: int = 0,
) -> list[str]:
    sents = _split_sentences(text)
    if not sents:
        return []

    snippets: list[str] = []
    seen = set()
    take_next = max(0, min(2, sentences) - 1)

    for i, s in enumerate(sents):
        if not rx.search(s):
            continue
        chunk = s
        if take_next and i + 1 < len(sents):
            chunk = f"{chunk} {sents[i + 1]}"
        # Optional: trim very long chunks (disabled by default).
        if snippet_max_chars and len(chunk) > snippet_max_chars:
            chunk = chunk[:snippet_max_chars].rstrip() + "…"
        key = chunk.lower()
        if key in seen:
            continue
        seen.add(key)
        snippets.append(chunk)
        if len(snippets) >= max_snippets:
            break

    return snippets


def _extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n\n".join(parts)


@dataclass(frozen=True)
class Hit:
    pdf: Path
    matches: int


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Find which PDFs contain a given word/phrase (extract text via pypdf; optional caching)."
    )
    ap.add_argument("query", help="Word or phrase to search for.")
    ap.add_argument(
        "-d",
        "--dir",
        default=".",
        help="Directory to scan recursively for PDFs (default: current dir).",
    )
    ap.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive search.")
    ap.add_argument("--whole-word", action="store_true", help="Match whole word boundaries.")
    ap.add_argument(
        "--sentences",
        type=int,
        default=2,
        choices=(1, 2),
        help="How many sentences to print per snippet when matched (1 or 2, default: 2).",
    )
    ap.add_argument(
        "--max-snippets",
        type=int,
        default=3,
        help="Max snippets to print per matched PDF (default: 3).",
    )
    ap.add_argument(
        "--snippet-max-chars",
        type=int,
        default=0,
        help="Max characters per snippet (0 = no limit, default: 0).",
    )
    ap.add_argument(
        "--cache-dir",
        default=".pdf_text_cache",
        help="Cache extracted PDF text to this directory (default: ./.pdf_text_cache).",
    )
    ap.add_argument("--no-cache", action="store_true", help="Disable cache; always extract from PDF.")
    args = ap.parse_args()

    base_dir = Path(args.dir).expanduser().resolve()
    if not base_dir.exists():
        print(f"Directory not found: {base_dir}")
        return 2

    pdfs = sorted(base_dir.rglob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found under: {base_dir}")
        return 0

    q = args.query
    flags = re.IGNORECASE if args.ignore_case else 0
    pat = re.escape(q)
    if args.whole_word:
        pat = r"\b" + pat + r"\b"
    rx = re.compile(pat, flags=flags)

    cache_dir = Path(args.cache_dir).expanduser().resolve()
    if not args.no_cache:
        cache_dir.mkdir(parents=True, exist_ok=True)

    hits: list[Hit] = []
    hit_snippets: dict[Path, list[str]] = {}
    scanned = 0
    for pdf in pdfs:
        scanned += 1
        try:
            cache_txt = cache_dir / f"{pdf.stem}.{_short_id(str(pdf))}.txt"
            if (not args.no_cache) and cache_txt.exists():
                text = cache_txt.read_text(encoding="utf-8", errors="ignore")
            else:
                text = _extract_pdf_text(pdf)
                if not args.no_cache:
                    cache_txt.write_text(text, encoding="utf-8")

            m = len(rx.findall(text))
            if m:
                hits.append(Hit(pdf=pdf, matches=m))
                hit_snippets[pdf] = _snippets_from_text(
                    rx,
                    text,
                    sentences=args.sentences,
                    max_snippets=max(0, args.max_snippets),
                    snippet_max_chars=max(0, args.snippet_max_chars),
                )
        except Exception as e:
            print(f"[SKIP] {pdf} ({e})")

    hits.sort(key=lambda h: (-h.matches, str(h.pdf).lower()))

    print(f"Scanned PDFs: {scanned}")
    print(f"Query: {q!r} (ignore_case={args.ignore_case}, whole_word={args.whole_word})")
    print(f"Hits: {len(hits)}")
    for h in hits:
        print(f"{h.matches:>5}  {h.pdf}")
        snippets = hit_snippets.get(h.pdf, [])
        for s in snippets:
            print(f"       - {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

