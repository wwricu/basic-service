import re
from html import escape

from bs4 import BeautifulSoup

from wwricu.domain.constant import CommonConst

# A CJK Unified Ideographs run, or a whole latin/digit run kept as one lowercased term.
cjk_pattern = re.compile(r'[一-龥]+|[a-zA-Z0-9]+')


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html or '', CommonConst.HTML_PARSER)
    for tag in soup.find_all(['script', 'style', 'pre']):
        tag.decompose()
    return ' '.join(soup.get_text().split())


def tokens(text: str) -> list[str]:
    result: list[str] = []
    for term in cjk_pattern.findall(text):
        if term[0].isascii():
            result.append(term.lower())
        else:  # CJK run: every overlapping bigram, a single char stays whole
            result += [term[i:i + 2] for i in range(len(term) - 1)] or [term]
    return result


def segment(text: str) -> str:
    return CommonConst.TOKEN_SEPARATOR.join(tokens(text))


def build_match(keyword: str) -> str:
    return ' AND '.join(f'"{t}"' for t in tokens(keyword))


def highlight(text: str, keyword: str, *, radius: int = 40) -> str:
    low = text.lower()
    needle = keyword.strip().lower()
    if needle not in low:
        needle = next((t for t in tokens(keyword) if t in low), '')
    pos = low.find(needle)
    if pos < 0:
        return escape(text[:radius * 2])
    start, end = max(pos - radius, 0), min(pos + len(needle) + radius, len(text))
    fragment = text[start:end]
    parts = re.split(f'({re.escape(needle)})', fragment, flags=re.IGNORECASE) if needle else [fragment]
    # odd parts are the captured hits; escape everything because the frontend injects the snippet as raw HTML
    marked = ''.join(f'<mark>{escape(p)}</mark>' if i % 2 else escape(p) for i, p in enumerate(parts))
    return f"{'…' if start else ''}{marked}{'…' if end < len(text) else ''}"