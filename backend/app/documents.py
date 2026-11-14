"""Document tools: loading, sectioning, chunking, BM25 retrieval, quote verification, number helpers."""
import hashlib
import io
import re

from rank_bm25 import BM25Okapi


# ------------------------------------------------------------------ loading
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def extract_text(filename: str, data: bytes) -> str:
    """Return plain text for a PDF / txt / md upload."""
    if filename.lower().endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n\n".join((p.extract_text() or "") for p in pdf.pages)
    return data.decode("utf-8", errors="replace")


# ------------------------------------------------------------------ sectioning
def _heading_re(title: str):
    # matches "## Financial Bid", "5. FINANCIAL BID", "Financial Bid:" at line start
    return re.compile(rf"^[ \t]*#*[ \t]*(?:\d+[.)][ \t]*)?{re.escape(title)}\b.*$", re.M | re.I)


def section(text: str, start: str, end: str | None = None) -> str:
    """Text between heading `start` and heading `end` ('' when `start` is absent)."""
    m = _heading_re(start).search(text)
    if not m:
        return ""
    rest = text[m.end():]
    if end:
        e = _heading_re(end).search(rest)
        if e:
            rest = rest[:e.start()]
    return rest.strip()


def section_or_all(text: str, start: str, end: str | None = None, limit: int = 14000) -> str:
    s = section(text, start, end)
    return (s if s else text)[:limit]


# ------------------------------------------------------------------ chunking + BM25
def chunk_document(text: str, max_words: int = 140):
    chunks, heading = [], "Document"
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            first, _, rest = block.partition("\n")
            heading = first.lstrip("# ").strip()
            block = rest.strip()
            if not block:
                continue
        words = block.split()
        for i in range(0, len(words), max_words):
            chunks.append(f"[{heading}] " + " ".join(words[i:i + max_words]))
    return chunks or [text[:2000]]


def tokenize(s: str):
    return re.findall(r"\w+", s.lower())


class Retriever:
    """Vectorless BM25 retrieval over bid chunks (every score can cite its chunk)."""

    def __init__(self, text: str):
        self.chunks = chunk_document(text)
        self.bm25 = BM25Okapi([tokenize(c) for c in self.chunks])

    def search(self, query: str, k: int = 3):
        scores = self.bm25.get_scores(tokenize(query))
        idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.chunks[i] for i in idx]


# ------------------------------------------------------------------ grounding check
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()


def verify_quote(quote: str, text: str) -> bool:
    """True when the quoted evidence really occurs in the document (anti-hallucination check)."""
    if not quote or not quote.strip():
        return False
    nt = _norm(text)
    parts = [p for p in re.split(r"\.\.\.|…", quote) if len(_norm(p)) >= 8]
    if not parts:
        return False
    return all(_norm(p) in nt for p in parts)


# ------------------------------------------------------------------ numbers
def to_num(x) -> float:
    if isinstance(x, (int, float)):
        return float(x)
    s = re.sub(r"[^\d.]", "", str(x))
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def inr(n: float) -> str:
    """Indian digit grouping: 45500000 -> 4,55,00,000."""
    s = str(int(round(n)))
    if len(s) <= 3:
        return s
    head, tail, parts = s[:-3], s[-3:], []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])
