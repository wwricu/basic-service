import re

from bs4 import BeautifulSoup

from wwricu.domain.constant import CommonConst


def extract_text(html: str) -> str:
    """Plain text of a post: drop script/style/pre and collapse whitespace; shared by index and snippet."""
    soup = BeautifulSoup(html or '', CommonConst.HTML_PARSER)
    for tag in soup.find_all(['script', 'style', 'pre']):
        tag.decompose()
    return ' '.join(soup.get_text().split())


def tokens(text: str) -> list[str]:
    """Emit a 2-gram per CJK run and keep latin/digit runs as one lowercased term. Dictionary-free, used by both indexing and querying."""
    result: list[str] = []
    for seg in cjk_pattern.findall(text):
        if '\u4e00' <= seg[0] <= '\u9fa5':  # run starts with a CJK char; range mirrors cjk_pattern above
            result += [seg] if len(seg) == 1 else [seg[i:i + 2] for i in range(len(seg) - 1)]
        else:
            result.append(seg.lower())
    return result


def segment(text: str) -> str:
    """Index writing: join tokens with the separator so FTS5 unicode61 splits them back into terms."""
    return CommonConst.TOKEN_SEPARATOR.join(tokens(text))


def build_match(keyword: str) -> str:
    """Query string: AND every token as a quoted phrase; avoids special-char injection and fixes the old over-broad OR."""
    return ' AND '.join(f'"{t}"' for t in tokens(keyword))


def highlight(text: str, keyword: str, *, radius: int = 40) -> str:
    """Locate the keyword in plain text, open a window around it and wrap the hit; falls back to the leading fragment when absent."""
    low, needle = text.lower(), keyword.strip().lower()
    if low.find(needle) < 0:
        needle = next((t for t in tokens(keyword) if low.find(t) >= 0), '')
    if (pos := low.find(needle)) < 0:
        return text[:radius * 2]
    start, end = max(pos - radius, 0), min(pos + len(needle) + radius, len(text))
    fragment = text[start:end]
    if needle:
        fragment = re.sub(f'({re.escape(needle)})', rf'{CommonConst.MARK_BEGIN}\1{CommonConst.MARK_END}', fragment, flags=re.IGNORECASE)
    return f"{ELLIPSIS if start else ''}{fragment}{ELLIPSIS if end < len(text) else ''}"


# \u4e00-\u9fa5 is the Unicode CJK Unified Ideographs block (covers common Chinese characters);
# the | alternation keeps a whole latin/digit run in one match so it can be lowercased as a single term.
cjk_pattern = re.compile(r'[\u4e00-\u9fa5]+|[a-zA-Z0-9]+')

# \u2026 is the horizontal ellipsis glyph; written as an escape so this source stays pure ASCII, same idea as the CJK range above.
ELLIPSIS = '\u2026'
