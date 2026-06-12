#!/usr/bin/env python3
"""Read and display the Firestore cancellationGuides collection for verification."""

from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from admin_tools.cancellation_discovery.firestore_writer import read_guides


def main() -> None:
    parser = argparse.ArgumentParser(description="Lire la collection Firestore cancellationGuides.")
    parser.add_argument("--project-id", help="ID du projet Google Cloud.")
    parser.add_argument("--json", action="store_true", help="Sortie JSON brute au lieu d'un résumé lisible.")
    args = parser.parse_args()

    documents = read_guides(project_id=args.project_id)

    if args.json:
        print(json.dumps(documents, ensure_ascii=False, indent=2))
        return

    print(f"{len(documents)} document(s) dans cancellationGuides\n")
    for doc in documents:
        print(f"- {doc.get('serviceName', '?')}  [{doc.get('documentId', '')}]")
        print(f"    statut: {doc.get('status', '')}  | confiance: {doc.get('confidenceScore', '')}  | catégorie: {doc.get('category', '')}")
        if doc.get("cancellationUrl"):
            print(f"    résiliation: {doc['cancellationUrl']}")


if __name__ == "__main__":
    main()
