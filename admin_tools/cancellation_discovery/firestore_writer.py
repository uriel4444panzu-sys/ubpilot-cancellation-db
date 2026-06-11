"""Firestore persistence for cancellation guides."""

from __future__ import annotations

from .models import CancellationGuide

COLLECTION_NAME = "cancellationGuides"


def write_guides(guides: list[CancellationGuide], project_id: str | None = None) -> None:
    """Upsert guides into Firestore using normalizedName as document id.

    Requires Application Default Credentials or GOOGLE_APPLICATION_CREDENTIALS. This module is
    imported only when --write-firestore is used so discovery/export can run without Google deps.
    """
    try:
        from google.cloud import firestore
    except ImportError as exc:
        raise RuntimeError("Install google-cloud-firestore to use --write-firestore.") from exc

    client = firestore.Client(project=project_id) if project_id else firestore.Client()
    batch = client.batch()
    pending = 0
    for guide in guides:
        doc_ref = client.collection(COLLECTION_NAME).document(guide.normalizedName)
        batch.set(doc_ref, guide.to_dict(), merge=True)
        pending += 1
        if pending == 450:
            batch.commit()
            batch = client.batch()
            pending = 0
    if pending:
        batch.commit()
    print(f"Wrote {len(guides)} documents to Firestore collection {COLLECTION_NAME}.")


def read_guides(project_id: str | None = None) -> list[dict]:
    """Read all documents from the Firestore cancellationGuides collection.

    Returns a list of plain dicts (each including the Firestore document id) so callers can
    verify what is currently stored without going through the Google console. Requires the same
    credentials as write_guides.
    """
    try:
        from google.cloud import firestore
    except ImportError as exc:
        raise RuntimeError("Install google-cloud-firestore to read Firestore.") from exc

    client = firestore.Client(project=project_id) if project_id else firestore.Client()
    documents = []
    for snapshot in client.collection(COLLECTION_NAME).stream():
        data = snapshot.to_dict() or {}
        data["documentId"] = snapshot.id
        documents.append(data)
    documents.sort(key=lambda item: (item.get("category", ""), str(item.get("serviceName", "")).lower()))
    return documents
