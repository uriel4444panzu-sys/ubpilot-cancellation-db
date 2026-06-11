"""Subscription categories supported by the admin discovery tool."""

CATEGORIES = {
    "streaming-video": "streaming vidéo",
    "musique": "musique",
    "sport-salles-de-sport": "sport / salles de sport",
    "telephonie-internet": "téléphonie / internet",
    "logiciels-saas": "logiciels / SaaS",
    "stockage-cloud": "stockage cloud",
    "jeux-video": "jeux vidéo",
    "presse-journaux": "presse / journaux",
    "box-mensuelles": "box mensuelles",
    "livraison-ecommerce": "livraison / e-commerce",
    "education-cours-en-ligne": "éducation / cours en ligne",
    "banques-assurances": "banques / assurances",
    "productivite": "productivité",
    "rencontres": "rencontres",
    "fitness-bien-etre": "fitness / bien-être",
}

DISCOVERY_QUERIES = [
    'site officiel abonnement {category} France',
    'meilleurs services abonnement {category} France',
    'services avec abonnement {category} résiliation compte client',
]

CATEGORY_SEEDS = {
    "streaming-video": ["Netflix", "Disney+", "Canal+", "Prime Video", "Max", "Paramount+", "Apple TV+", "Crunchyroll"],
    "musique": ["Spotify", "Deezer", "Apple Music", "YouTube Music", "Qobuz", "Tidal", "Amazon Music"],
    "sport-salles-de-sport": ["Basic-Fit", "Fitness Park", "Keepcool", "Neoness", "L'Orange Bleue", "ClassPass"],
    "telephonie-internet": ["Orange", "SFR", "Bouygues Telecom", "Free", "Sosh", "RED by SFR", "B&You"],
    "logiciels-saas": ["Adobe", "Microsoft 365", "Canva", "Notion", "Dropbox", "Slack", "Zoom"],
    "stockage-cloud": ["Google One", "iCloud+", "Dropbox", "pCloud", "kDrive", "OneDrive", "Box"],
    "jeux-video": ["Xbox Game Pass", "PlayStation Plus", "Nintendo Switch Online", "GeForce NOW", "EA Play", "Ubisoft+"],
    "presse-journaux": ["Le Monde", "Le Figaro", "Mediapart", "Libération", "Les Echos", "Ouest-France"],
    "box-mensuelles": ["My Little Box", "Birchbox", "Gambettes Box", "Le Petit Ballon", "Woufbox", "Glossybox"],
    "livraison-ecommerce": ["Amazon Prime", "Deliveroo Plus", "Uber One", "Carrefour Plus", "Cdiscount à volonté"],
    "education-cours-en-ligne": ["OpenClassrooms", "Coursera", "Udemy", "Babbel", "Duolingo", "Skillshare"],
    "banques-assurances": ["Revolut", "N26", "Boursorama", "Qonto", "Luko", "Alan"],
    "productivite": ["Todoist", "Evernote", "Trello", "Asana", "Monday.com", "ClickUp", "Grammarly"],
    "rencontres": ["Tinder", "Meetic", "Bumble", "Happn", "Adopte", "DisonsDemain"],
    "fitness-bien-etre": ["Strava", "Headspace", "Calm", "Freeletics", "Fitbit Premium", "MyFitnessPal"],
}
