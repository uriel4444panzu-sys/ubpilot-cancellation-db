"""Public-web search helpers.

The tool intentionally uses only public search result pages and public URLs. It never logs in,
solves captchas, bypasses paywalls, or attempts protected account flows.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urlencode, urlparse
from urllib.request import Request, urlopen
import json
import re
import time

# A realistic browser User-Agent: DuckDuckGo returns 403 for obvious bot agents.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""


class _ResultParser(HTMLParser):
    """Parse the structured DuckDuckGo html result page (anchors with class result__a)."""

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


class _AnchorParser(HTMLParser):
    """Fallback parser: collect every external result link (covers the lite endpoint layout)."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[SearchResult] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            url = clean_result_url(self._href)
            title = " ".join(piece.strip() for piece in self._text if piece.strip())
            if url and _is_external(url):
                self.results.append(SearchResult(title=title or url, url=url))
            self._href = None
            self._text = []


def _is_external(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc) and "duckduckgo.com" not in parsed.netloc.lower()


def _http(url: str, data: bytes | None = None) -> str:
    """Fetch a public URL (GET, or POST when data is given) without cookies or auth."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = Request(url, data=data, headers=headers)  # nosec: admin tool uses public pages only
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        content_type = response.headers.get("content-type", "")
        raw = response.read(1_000_000)
    if "charset=" in content_type:
        charset = content_type.split("charset=", 1)[1].split(";", 1)[0]
    else:
        charset = "utf-8"
    return raw.decode(charset, errors="replace")


def fetch_url(url: str) -> str:
    """Fetch a public URL without cookies or authenticated state."""
    return _http(url)


def clean_result_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    # DuckDuckGo wraps targets as /l/?uddg=<encoded-url> (html and lite endpoints).
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(target)
    return url


def _parse_results(html: str) -> list[SearchResult]:
    structured = _ResultParser()
    structured.feed(html)
    if structured.results:
        return structured.results
    fallback = _AnchorParser()
    fallback.feed(html)
    return fallback.results


def search_web(query: str, limit: int = 10, pause_seconds: float = 1.0) -> list[SearchResult]:
    """Search DuckDuckGo and return public result URLs.

    Several endpoints/methods are tried in turn (POST html, GET html, GET lite) because DuckDuckGo
    intermittently blocks scrapers. If all fail or markup changes, the caller receives an empty
    list and can continue with seed services, curated examples, or manual review.
    """
    encoded = quote_plus(query)
    attempts: list[tuple[str, bytes | None]] = [
        ("https://html.duckduckgo.com/html/", urlencode({"q": query}).encode("utf-8")),
        (f"https://html.duckduckgo.com/html/?q={encoded}", None),
        (f"https://lite.duckduckgo.com/lite/?q={encoded}", None),
    ]
    results: list[SearchResult] = []
    for url, data in attempts:
        try:
            html = _http(url, data=data)
        except Exception:
            continue
        results = _parse_results(html)
        if results:
            break
    time.sleep(max(0.0, pause_seconds))

    seen: set[str] = set()
    unique: list[SearchResult] = []
    for result in results:
        if result.url not in seen:
            seen.add(result.url)
            unique.append(result)
    return unique[:limit]


def official_website_from_wikidata(name: str) -> str:
    """Resolve a brand's official website via the public Wikidata API (property P856).

    This is more reliable than scraping a search engine for the home page and is not blocked by
    bot protection. Returns "" on any failure so callers can fall back to search or manual entry.
    """
    if not name.strip():
        return ""
    try:
        search_url = "https://www.wikidata.org/w/api.php?" + urlencode(
            {"action": "wbsearchentities", "search": name, "language": "fr",
             "uselang": "fr", "format": "json", "type": "item", "limit": "1"}
        )
        hits = json.loads(_http(search_url)).get("search", [])
        if not hits:
            return ""
        entity_id = hits[0]["id"]
        claims_url = "https://www.wikidata.org/w/api.php?" + urlencode(
            {"action": "wbgetentities", "ids": entity_id, "props": "claims", "format": "json"}
        )
        entity = json.loads(_http(claims_url)).get("entities", {}).get(entity_id, {})
        for claim in entity.get("claims", {}).get("P856", []):
            value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
    except Exception:
        return ""
    return ""


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
