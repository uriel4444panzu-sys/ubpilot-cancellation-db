# Authentification Firestore — guide pas à pas

Ce guide explique comment connecter l'outil admin à la base Firestore du projet
**`subpilot-bd743`**, en créant un compte de service et sa clé JSON.

Tu n'as besoin de faire ceci **qu'une seule fois** sur ton ordinateur.

---

## 1. Installer la librairie Google

Dans le dossier du projet :

```bash
pip install -r requirements.txt
# ou directement :
pip install google-cloud-firestore
```

## 2. Créer un compte de service

1. Ouvre la console Google Cloud : https://console.cloud.google.com/iam-admin/serviceaccounts?project=subpilot-bd743
2. Vérifie en haut que le projet sélectionné est bien **subpilot-bd743**.
3. Clique sur **« + Créer un compte de service »**.
4. Nom : par exemple `subpilot-admin-cancellation`. Clique **« Créer et continuer »**.
5. À l'étape « Accorder l'accès », choisis le rôle :
   - **Cloud Datastore User** (`roles/datastore.user`) — suffisant pour lire et écrire Firestore.
6. Clique **« Continuer »** puis **« OK / Terminer »**.

> Pourquoi ce rôle et pas « Propriétaire » : on limite le compte à Firestore uniquement,
> par sécurité. Si tu veux seulement vérifier le contenu sans écrire, le rôle
> **Cloud Datastore Viewer** (`roles/datastore.viewer`) suffit.

## 3. Générer la clé JSON

1. Dans la liste, clique sur le compte de service que tu viens de créer.
2. Onglet **« Clés »** → **« Ajouter une clé »** → **« Créer une clé »**.
3. Type **JSON** → **« Créer »**. Un fichier `.json` se télécharge automatiquement.
4. **Range ce fichier dans un endroit sûr, hors du dépôt Git.** Ne le partage jamais et
   ne le commit jamais (c'est l'équivalent d'un mot de passe).

> Astuce : si tu veux le garder dans le projet, mets-le dans un dossier `secrets/`
> (déjà ignoré par Git) — par exemple `secrets/subpilot-sa-key.json`.

## 4. Indiquer la clé à l'outil

Avant de lancer l'interface ou les scripts, définis la variable d'environnement qui pointe
vers ta clé :

```bash
# macOS / Linux
export GOOGLE_APPLICATION_CREDENTIALS="/chemin/vers/ta-cle.json"

# Windows (PowerShell)
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\chemin\vers\ta-cle.json"
```

> Alternative sans clé JSON (si tu as l'outil `gcloud` installé) :
> `gcloud auth application-default login` puis
> `gcloud config set project subpilot-bd743`.

## 5. Vérifier que ça marche

Lis le contenu actuel de la collection :

```bash
python scripts/read_firestore.py --project-id subpilot-bd743
```

- Si la base est vide, tu verras `0 document(s)` — c'est normal au début.
- Si tu vois une erreur d'authentification, revérifie l'étape 4 (chemin de la clé) et
  l'étape 2 (le rôle accordé).

Ensuite, lance l'interface web et utilise les boutons « Écrire dans Firestore » /
« Charger le contenu Firestore » :

```bash
python scripts/web.py
```

## 6. Déployer les règles de sécurité (recommandé)

Le fichier [`firestore.rules`](../firestore.rules) limite l'accès des clients à la collection.
Avec la Firebase CLI :

```bash
firebase deploy --only firestore:rules --project subpilot-bd743
```

Pense à fusionner avec tes règles SubPilot existantes : ce fichier ne couvre que
`cancellationGuides`.

---

## Sécurité — à retenir

- La clé JSON = un secret. Ne la commit jamais (le `.gitignore` bloque déjà les noms courants,
  mais reste vigilant).
- Si une clé fuite, supprime-la dans la console (onglet « Clés » du compte de service) et
  génère-en une nouvelle.
- Le compte de service contourne les règles de sécurité Firestore : n'accorde que le rôle
  minimal nécessaire.
