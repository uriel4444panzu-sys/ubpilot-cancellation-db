"""Data model helpers for cancellation guide discovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
