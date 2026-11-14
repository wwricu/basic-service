import re
from html import escape

from bs4 import BeautifulSoup

from wwricu.domain.constant import CommonConst


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html or '', CommonConst.HTML_PARSER)
    for tag in soup.find_all(['script', 'style', 'pre']):
        tag.decompose()
    return ' '.join(soup.get_text().split())


def tokens(text: str) -> list[str]:
    result: list[str] = []
    for seg in cjk_pattern.findall(text):
        if '\u4e00' <= seg[0] <= '\u9fa5':  # run starts with a CJK char; range mirrors cjk_pattern above
            result += [seg] if len(seg) == 1 else [seg[i:i + 2] for i in range(len(seg) - 1)]
        else:
            result.append(seg.lower())
    return result


def segment(text: str) -> str:
    return CommonConst.TOKEN_SEPARATOR.join(tokens(text))


def build_match(keyword: str) -> str:
    return ' AND '.join(f'"{t}"' for t in tokens(keyword))


def highlight(text: str, keyword: str, *, radius: int = 40) -> str:
    low, needle = text.lower(), keyword.strip().lower()
    if low.find(needle) < 0:
        needle = next((t for t in tokens(keyword) if low.find(t) >= 0), '')
    if (pos := low.find(needle)) < 0:
        return escape(text[:radius * 2])
    start, end = max(pos - radius, 0), min(pos + len(needle) + radius, len(text))
    fragment = text[start:end]
    parts = re.split(f'({re.escape(needle)})', fragment, flags=re.IGNORECASE) if needle else [fragment]
    # odd parts are the captured hits; everything is escaped because the frontend injects the snippet as raw HTML
    marked = ''.join(escape(p) if i % 2 == 0 else f'{CommonConst.MARK_BEGIN}{escape(p)}{CommonConst.MARK_END}'
                     for i, p in enumerate(parts))
    return f"{'\u2026' if start else ''}{marked}{'\u2026' if end < len(text) else ''}"


# \u4e00-\u9fa5 is the Unicode CJK Unified Ideographs block (covers common Chinese characters);
# the | alternation keeps a whole latin/digit run in one match so it can be lowercased as a single term.
cjk_pattern = re.compile(r'[\u4e00-\u9fa5]+|[a-zA-Z0-9]+')
