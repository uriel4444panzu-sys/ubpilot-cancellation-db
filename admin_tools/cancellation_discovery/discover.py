"""Discover subscription services by category."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from .categories import CATEGORIES, CATEGORY_SEEDS, DISCOVERY_QUERIES
from .models import CancellationGuide, normalize_name
from .search import search_web

BLOCKED_DOMAINS = {
    "facebook.com", "instagram.com", "x.com", "twitter.com", "linkedin.com", "youtube.com",
    "wikipedia.org", "reddit.com", "trustpilot.com", "apple.com", "play.google.com",
}


def likely_service_name(title: str) -> str:
    separators = [" | ", " - ", " — ", ": "]
    cleaned = title.strip()
    for sep in separators:
        if sep in cleaned:
            cleaned = cleaned.split(sep, 1)[0]
            break
    return cleaned.strip(" .•")[:80]


def is_usable_domain(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return bool(host) and not any(host == domain or host.endswith(f".{domain}") for domain in BLOCKED_DOMAINS)


def discover_category(category_key: str, limit_per_query: int = 8, include_seeds: bool = True) -> list[CancellationGuide]:
    if category_key not in CATEGORIES:
        raise ValueError(f"Unknown category '{category_key}'. Valid values: {', '.join(CATEGORIES)}")

    category_label = CATEGORIES[category_key]
    discovered: dict[str, CancellationGuide] = {}

    if include_seeds:
        for service in CATEGORY_SEEDS.get(category_key, []):
            discovered[normalize_name(service)] = CancellationGuide.from_partial(
                service,
                category_label,
                confidenceScore=0.55,
                status="needs_review",
                notes="Seed service; run verification to collect official links.",
            )

    for template in DISCOVERY_QUERIES:
        query = template.format(category=category_label)
        for result in search_web(query, limit=limit_per_query):
            if not is_usable_domain(result.url):
                continue
            service_name = likely_service_name(result.title)
            normalized = normalize_name(service_name)
            if not service_name or len(service_name) < 2:
                continue
            current = discovered.get(normalized)
            if current:
                if result.url not in current.sourceUrls:
                    current.sourceUrls.append(result.url)
                if not current.officialWebsite:
                    current.officialWebsite = result.url
                current.confidenceScore = min(0.85, current.confidenceScore + 0.05)
            else:
                discovered[normalized] = CancellationGuide.from_partial(
                    service_name,
                    category_label,
                    officialWebsite=result.url,
                    sourceUrls=[result.url],
                    confidenceScore=0.45,
                    status="needs_review",
                    notes=f"Discovered from public search query: {query}",
                )
    return sorted(discovered.values(), key=lambda guide: (guide.category, guide.serviceName.lower()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover subscription services by category for SubPilot admin review.")
    parser.add_argument("--category", choices=sorted(CATEGORIES), help="Limit discovery to one category.")
    parser.add_argument("--all", action="store_true", help="Run discovery for every category.")
    parser.add_argument("--output", default="examples/discovered-services.json", help="JSON output path.")
    parser.add_argument("--limit-per-query", type=int, default=8, help="Maximum search results consumed per category query.")
    parser.add_argument("--no-seeds", action="store_true", help="Disable built-in example seed services.")
    args = parser.parse_args()

    if not args.category and not args.all:
        parser.error("Use --category <key> or --all.")

    category_keys = [args.category] if args.category else sorted(CATEGORIES)
    guides: list[CancellationGuide] = []
    for category_key in category_keys:
        guides.extend(discover_category(category_key, args.limit_per_query, include_seeds=not args.no_seeds))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps([guide.to_dict() for guide in guides], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(guides)} discovered service candidates to {output_path}")


if __name__ == "__main__":
    main()
