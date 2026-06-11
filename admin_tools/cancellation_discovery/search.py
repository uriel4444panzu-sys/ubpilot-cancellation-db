"""Public-web search helpers.

The tool intentionally uses only public search result pages and public URLs. It never logs in,
solves captchas, bypasses paywalls, or attempts protected account flows.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen
import json
import re
import time

USER_AGENT = "SubPilotCancellationDiscovery/0.1 (+admin research; public pages only)"
TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""


class _DuckDuckGoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[SearchResult] = []
        self._in_anchor = False
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a" and attrs_dict.get("class", "").find("result__a") >= 0:
            self._in_anchor = True
            self._href = attrs_dict.get("href") or ""
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._in_anchor:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_anchor:
            title = " ".join(piece.strip() for piece in self._text if piece.strip())
            url = clean_result_url(self._href)
            if title and url:
                self.results.append(SearchResult(title=title, url=url))
            self._in_anchor = False
            self._href = ""
            self._text = []


def fetch_url(url: str) -> str:
    """Fetch a public URL without cookies or authenticated state."""
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7"})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # nosec: admin CLI uses operator-provided/public URLs
        content_type = response.headers.get("content-type", "")
        raw = response.read(1_000_000)
    if "charset=" in content_type:
        charset = content_type.split("charset=", 1)[1].split(";", 1)[0]
    else:
        charset = "utf-8"
    return raw.decode(charset, errors="replace")


def clean_result_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(target)
    return url


def search_web(query: str, limit: int = 10, pause_seconds: float = 1.0) -> list[SearchResult]:
    """Search DuckDuckGo HTML and return public result URLs.

    If DuckDuckGo blocks or changes markup, the caller receives an empty list and can continue
    with seed services or manual review.
    """
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        html = fetch_url(url)
    except Exception:
        return []
    parser = _DuckDuckGoParser()
    parser.feed(html)
    time.sleep(max(0.0, pause_seconds))
    return parser.results[:limit]


def extract_json_ld_names(html: str) -> list[str]:
    names: list[str] = []
    for match in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
        try:
            payload = json.loads(match.group(1).strip())
        except Exception:
            continue
        objects = payload if isinstance(payload, list) else [payload]
        for item in objects:
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                names.append(item["name"])
    return names
