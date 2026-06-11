"""Verify public subscription-management and cancellation links for discovered services."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from urllib.parse import urlparse

from .categories import CATEGORIES
from .curated_examples import CURATED_EXAMPLES
from .models import CancellationGuide, normalize_name, now_iso
from .search import SearchResult, search_web

LINK_QUERIES = {
    "officialWebsite": ["{service} site officiel France"],
    "loginUrl": ["{service} connexion compte client", "{service} login account"],
    "manageSubscriptionUrl": ["{service} gérer abonnement compte", "{service} manage subscription"],
    "cancellationUrl": ["{service} résilier abonnement aide officielle", "{service} cancel subscription help"],
    "helpUrl": ["{service} centre aide officiel", "{service} help center official"],
}

OFFICIAL_HINTS = ("help", "support", "assistance", "aide", "account", "compte", "login", "connexion", "abonnement", "subscription", "resilier", "cancel")

EXAMPLE_SERVICES = [
    {"serviceName": "Netflix", "category": "streaming vidéo"},
    {"serviceName": "Spotify", "category": "musique"},
    {"serviceName": "Disney+", "category": "streaming vidéo"},
    {"serviceName": "Basic-Fit", "category": "sport / salles de sport"},
    {"serviceName": "Orange", "category": "téléphonie / internet"},
    {"serviceName": "Adobe", "category": "logiciels / SaaS"},
]


def domain_root(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def choose_best_result(results: list[SearchResult], service: str, known_domain: str = "") -> str:
    service_token = normalize_name(service).split("-")[0]
    known_root = domain_root(known_domain) if known_domain else ""
    ranked: list[tuple[int, str]] = []
    for result in results:
        url = result.url
        host = urlparse(url).netloc.lower()
        text = f"{result.title} {url}".lower()
        score = 0
        if known_root and known_root in host:
            score += 8
        if service_token and service_token in host:
            score += 5
        if any(hint in text for hint in OFFICIAL_HINTS):
            score += 2
        if "official" in text or "officiel" in text:
            score += 1
        if host and not any(blocked in host for blocked in ["reddit", "wikipedia", "trustpilot", "facebook", "youtube"]):
            score += 1
        ranked.append((score, url))
    ranked.sort(reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] >= 3 else ""


def verify_service(service_name: str, category: str, official_website: str = "", country: str = "FR") -> CancellationGuide:
    curated = CURATED_EXAMPLES.get(normalize_name(service_name), {})
    initial_official = official_website or curated.get("officialWebsite", "")
    guide = CancellationGuide.from_partial(
        service_name,
        category,
        country=country,
        officialWebsite=initial_official,
        loginUrl=curated.get("loginUrl", ""),
        manageSubscriptionUrl=curated.get("manageSubscriptionUrl", ""),
        cancellationUrl=curated.get("cancellationUrl", ""),
        helpUrl=curated.get("helpUrl", ""),
        confidenceScore=0.0,
        status="not_found",
        notes="Verified from public search results only; no login, captcha, paywall, or protected flow was accessed.",
    )
    if curated.get("notes"):
        guide.notes = f"{guide.notes} {curated['notes']}"
    sources: set[str] = {url for url in [guide.officialWebsite, guide.loginUrl, guide.manageSubscriptionUrl, guide.cancellationUrl, guide.helpUrl] if url}

    for field_name, queries in LINK_QUERIES.items():
        if getattr(guide, field_name):
            continue
        best_url = ""
        for template in queries:
            results = search_web(template.format(service=service_name), limit=6)
            best_url = choose_best_result(results, service_name, guide.officialWebsite)
            if best_url:
                break
        setattr(guide, field_name, best_url)
        if best_url:
            sources.add(best_url)

    guide.sourceUrls = sorted(sources)
    found_count = sum(bool(getattr(guide, field)) for field in ["officialWebsite", "loginUrl", "manageSubscriptionUrl", "cancellationUrl", "helpUrl"])
    same_domain_links = 0
    root = domain_root(guide.officialWebsite) if guide.officialWebsite else ""
    if root:
        same_domain_links = sum(root in domain_root(url) for url in [guide.loginUrl, guide.manageSubscriptionUrl, guide.cancellationUrl, guide.helpUrl] if url)
    guide.confidenceScore = min(0.98, 0.18 * found_count + 0.05 * same_domain_links)
    if guide.cancellationUrl and guide.confidenceScore >= 0.70:
        guide.status = "verified"
    elif found_count > 0:
        guide.status = "needs_review"
    else:
        guide.status = "not_found"
    guide.lastCheckedAt = now_iso()
    return guide


def load_input(path: str | None, examples: bool) -> list[dict]:
    if examples:
        return EXAMPLE_SERVICES
    if not path:
        raise ValueError("Provide --input or --examples.")
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of service objects.")
    return data


def guides_to_json_str(guides: list[CancellationGuide]) -> str:
    return json.dumps([guide.to_dict() for guide in guides], ensure_ascii=False, indent=2) + "\n"


def guides_to_csv_str(guides: list[CancellationGuide]) -> str:
    rows = [guide.to_dict() for guide in guides]
    fieldnames = list(rows[0].keys()) if rows else list(CancellationGuide.from_partial("example", "example").to_dict().keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        row = dict(row)
        row["sourceUrls"] = "|".join(row["sourceUrls"])
        writer.writerow(row)
    return buffer.getvalue()


def write_json(guides: list[CancellationGuide], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(guides_to_json_str(guides), encoding="utf-8")


def write_csv(guides: list[CancellationGuide], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(guides_to_csv_str(guides), encoding="utf-8", newline="")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify public cancellation and account links for subscription services.")
    parser.add_argument("--input", help="JSON file produced by discover_services.py or a compatible list.")
    parser.add_argument("--service", help="Verify or re-check one service name only.")
    parser.add_argument("--category", choices=sorted(CATEGORIES), help="Category key for --service, or filter input services by category key/label.")
    parser.add_argument("--examples", action="store_true", help="Verify built-in examples: Netflix, Spotify, Disney+, Basic-Fit, Orange, Adobe.")
    parser.add_argument("--output-json", default="examples/verified-guides.json", help="JSON export path.")
    parser.add_argument("--output-csv", help="Optional CSV export path.")
    parser.add_argument("--write-firestore", action="store_true", help="Write verified results to Firestore cancellationGuides.")
    parser.add_argument("--project-id", help="Google Cloud project id for Firestore writes.")
    parser.add_argument("--country", default="FR", help="Country code stored in Firestore; default FR.")
    args = parser.parse_args()

    if args.service:
        category = CATEGORIES.get(args.category or "", args.category or "needs_review")
        items = [{"serviceName": args.service, "category": category}]
    else:
        items = load_input(args.input, args.examples)
        if args.category:
            label = CATEGORIES[args.category]
            items = [item for item in items if item.get("category") in {args.category, label}]

    guides = [
        verify_service(
            item["serviceName"],
            item.get("category", "needs_review"),
            item.get("officialWebsite", ""),
            args.country,
        )
        for item in items
    ]
    write_json(guides, args.output_json)
    if args.output_csv:
        write_csv(guides, args.output_csv)
    if args.write_firestore:
        from .firestore_writer import write_guides

        write_guides(guides, project_id=args.project_id)
    print(f"Verified {len(guides)} services. JSON: {args.output_json}")
    if args.output_csv:
        print(f"CSV: {args.output_csv}")


if __name__ == "__main__":
    main()
