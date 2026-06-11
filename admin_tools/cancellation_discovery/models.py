"""Data model helpers for cancellation guide discovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
import re
import unicodedata

VALID_STATUSES = {"verified", "needs_review", "not_found"}


def now_iso() -> str:
    """Return an ISO-8601 UTC timestamp for Firestore-friendly exports."""
    return datetime.now(timezone.utc).isoformat()


def normalize_name(name: str) -> str:
    """Normalize a service name into a stable Firestore document id candidate."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug or "unknown-service"


@dataclass
class CancellationGuide:
    serviceName: str
    normalizedName: str
    category: str
    country: str = "FR"
    officialWebsite: str = ""
    loginUrl: str = ""
    manageSubscriptionUrl: str = ""
    cancellationUrl: str = ""
    helpUrl: str = ""
    sourceUrls: list[str] = field(default_factory=list)
    confidenceScore: float = 0.0
    status: str = "needs_review"
    lastCheckedAt: str = field(default_factory=now_iso)
    notes: str = ""

    def to_dict(self) -> dict:
        """Serialize the guide using the exact Firestore field names."""
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")
        data = asdict(self)
        data["confidenceScore"] = round(float(data["confidenceScore"]), 3)
        return data

    @classmethod
    def from_partial(cls, service_name: str, category: str, **kwargs) -> "CancellationGuide":
        return cls(
            serviceName=service_name,
            normalizedName=normalize_name(service_name),
            category=category,
            **kwargs,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "CancellationGuide":
        """Rebuild a guide from a (possibly edited) plain dict, e.g. from the web UI."""
        allowed = {f.name for f in fields(cls)}
        clean = {key: value for key, value in data.items() if key in allowed}
        service_name = (clean.get("serviceName") or "").strip()
        if not service_name:
            raise ValueError("serviceName is required.")
        clean["serviceName"] = service_name
        clean["normalizedName"] = normalize_name(clean.get("normalizedName") or service_name)
        clean["category"] = clean.get("category") or "needs_review"
        clean.setdefault("country", "FR")
        clean["sourceUrls"] = list(clean.get("sourceUrls") or [])
        try:
            clean["confidenceScore"] = round(float(clean.get("confidenceScore", 0.0)), 3)
        except (TypeError, ValueError):
            clean["confidenceScore"] = 0.0
        if clean.get("status") not in VALID_STATUSES:
            clean["status"] = "needs_review"
        return cls(**clean)
