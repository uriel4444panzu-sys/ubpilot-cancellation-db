# ubpilot-cancellation-db

Outils admin séparés pour construire une base Firestore de guides de gestion et résiliation d'abonnements pour SubPilot.

## Démarrage rapide

```bash
python scripts/discover_services.py --category streaming-video --output examples/discovered-streaming.json
python scripts/verify_cancellation_links.py --examples --output-json examples/verified-examples.json --output-csv examples/verified-examples.csv
```

Documentation complète : [`docs/admin-cancellation-discovery.md`](docs/admin-cancellation-discovery.md).
