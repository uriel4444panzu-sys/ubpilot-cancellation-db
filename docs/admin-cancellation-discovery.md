# Outil admin de découverte des services d'abonnement

Cet outil est séparé de l'application principale SubPilot. Il sert à alimenter et vérifier la collection Firestore `cancellationGuides` à partir d'informations publiques.

## Règles de sécurité et de conformité

- Ne jamais se connecter à un compte utilisateur.
- Ne jamais contourner un login, un paywall, un captcha, une protection anti-bot ou une restriction technique.
- Ne collecter que des URL et informations publiques.
- Privilégier les sources officielles : site officiel, compte client public, centre d'aide, assistance.
- Marquer `needs_review` dès qu'un lien n'est pas suffisamment sûr.
- Ne pas exposer dans SubPilot les documents `needs_review` tant qu'un administrateur ne les a pas validés.

## Schéma Firestore

Collection : `cancellationGuides`

Chaque document utilise `normalizedName` comme identifiant stable et contient :

- `serviceName`
- `normalizedName`
- `category`
- `country` (`FR` par défaut)
- `officialWebsite`
- `loginUrl`
- `manageSubscriptionUrl`
- `cancellationUrl`
- `helpUrl`
- `sourceUrls`
- `confidenceScore`
- `status` : `verified`, `needs_review` ou `not_found`
- `lastCheckedAt`
- `notes`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`google-cloud-firestore` n'est requis que pour l'écriture Firestore. La découverte, la vérification et les exports JSON/CSV utilisent la bibliothèque standard Python.

## Interface web (sans ligne de commande)

Si tu préfères travailler dans une vraie interface, lance le serveur local :

```bash
python scripts/web.py
```

Le navigateur s'ouvre sur `http://127.0.0.1:8000/`. La page regroupe tout le workflow :

1. **Découverte** — coche une ou plusieurs catégories, règle le nombre de résultats par requête,
   inclus ou non les services connus (seeds), puis lance la découverte.
2. **Vérification & révision** — vérifie les liens (tous ou un seul service), édite directement
   chaque lien et chaque note dans le tableau, et bascule le statut `verified` / `needs_review` /
   `not_found` à la main.
3. **Export & Firestore** — télécharge le résultat en JSON ou CSV, ou écris-le dans la collection
   Firestore `cancellationGuides`.
4. **Voir le contenu Firestore** — lit la collection `cancellationGuides` telle qu'elle est stockée
   pour vérifier le contenu sans passer par la console Google. Bouton « Copier dans le tableau
   d'édition » pour réviser/re-vérifier des documents existants.

Options du serveur :

- `--port 8000` change le port d'écoute.
- `--host 127.0.0.1` change l'adresse d'écoute (laisse `127.0.0.1` pour un usage local privé).
- `--no-browser` ne lance pas le navigateur automatiquement.

Le serveur utilise uniquement la bibliothèque standard Python : aucune dépendance supplémentaire.
Comme la version en ligne de commande, il ne lit que des pages et URL publiques (aucun login,
captcha ou paywall contourné). Pour l'écriture Firestore, installe `google-cloud-firestore` et
configure les identifiants (ADC ou `GOOGLE_APPLICATION_CREDENTIALS`).

## Catégories disponibles

- `streaming-video` — streaming vidéo
- `musique` — musique
- `sport-salles-de-sport` — sport / salles de sport
- `telephonie-internet` — téléphonie / internet
- `logiciels-saas` — logiciels / SaaS
- `stockage-cloud` — stockage cloud
- `jeux-video` — jeux vidéo
- `presse-journaux` — presse / journaux
- `box-mensuelles` — box mensuelles
- `livraison-ecommerce` — livraison / e-commerce
- `education-cours-en-ligne` — éducation / cours en ligne
- `banques-assurances` — banques / assurances
- `productivite` — productivité
- `rencontres` — rencontres
- `fitness-bien-etre` — fitness / bien-être

## Étape 1 : découverte automatique par catégorie

Découvrir une seule catégorie :

```bash
python scripts/discover_services.py --category streaming-video --output examples/discovered-streaming.json
```

Découvrir toutes les catégories :

```bash
python scripts/discover_services.py --all --output examples/discovered-services.json
```

Options utiles :

- `--category <key>` limite la recherche à une catégorie.
- `--all` lance toutes les catégories.
- `--limit-per-query 5` limite le nombre de résultats de recherche consommés par requête.
- `--no-seeds` désactive les exemples intégrés connus et ne garde que les résultats découverts via recherche publique.

## Étape 2 : vérification des liens de gestion/résiliation

Vérifier un fichier issu de la découverte :

```bash
python scripts/verify_cancellation_links.py --input examples/discovered-services.json --output-json examples/verified-guides.json --output-csv examples/verified-guides.csv
```

Relancer la vérification d'un service précis :

```bash
python scripts/verify_cancellation_links.py --service Netflix --category streaming-video --output-json examples/netflix.json
```

Limiter une vérification à une catégorie :

```bash
python scripts/verify_cancellation_links.py --input examples/discovered-services.json --category musique --output-json examples/verified-music.json
```

Lancer les exemples demandés : Netflix, Spotify, Disney+, Basic-Fit, Orange et Adobe.

```bash
python scripts/verify_cancellation_links.py --examples --output-json examples/verified-examples.json --output-csv examples/verified-examples.csv
```

## Écriture Firestore

Authentifiez d'abord l'environnement avec Application Default Credentials ou `GOOGLE_APPLICATION_CREDENTIALS`, puis ajoutez `--write-firestore` :

```bash
python scripts/verify_cancellation_links.py --input examples/discovered-services.json --write-firestore --project-id <gcp-project-id>
```

L'écriture est un upsert dans la collection `cancellationGuides`, avec `normalizedName` comme identifiant de document.

## Lecture / vérification Firestore

Pour vérifier ce qui est réellement stocké, sans passer par la console Google :

```bash
python scripts/read_firestore.py --project-id <gcp-project-id>
python scripts/read_firestore.py --project-id <gcp-project-id> --json
```

La même lecture est disponible dans l'interface web (section « Voir le contenu Firestore »).
La lecture nécessite les mêmes identifiants que l'écriture.

## Workflow recommandé

1. Lancer la découverte sur une catégorie ou toutes les catégories.
2. Vérifier les liens détectés.
3. Inspecter manuellement les documents `needs_review`.
4. Ne passer à `verified` que les services dont les liens officiels sont confirmés.
5. Exporter JSON/CSV pour audit ou écrire dans Firestore.
6. Côté application SubPilot, filtrer strictement sur `status == "verified"` avant affichage utilisateur.
