# ubpilot-cancellation-db

Outils admin séparés pour construire une base Firestore de guides de gestion et résiliation d'abonnements pour SubPilot.

## Interface web (recommandé)

Pour utiliser l'outil dans une vraie interface plutôt qu'en ligne de commande :

```bash
python scripts/web.py
```

Le navigateur s'ouvre automatiquement sur `http://127.0.0.1:8000/`. Depuis cette page tu peux,
à la souris : choisir des catégories et lancer la découverte, vérifier les liens, éditer/valider
les statuts `verified` / `needs_review` / `not_found`, puis exporter en JSON/CSV ou écrire dans
Firestore. Aucune dépendance supplémentaire à installer (serveur web intégré de Python).

## Démarrage rapide (ligne de commande)

```bash
python scripts/discover_services.py --category streaming-video --output examples/discovered-streaming.json
python scripts/verify_cancellation_links.py --examples --output-json examples/verified-examples.json --output-csv examples/verified-examples.csv
```

Documentation complète : [`docs/admin-cancellation-discovery.md`](docs/admin-cancellation-discovery.md).
