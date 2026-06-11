"""Curated public official-link examples used as safe fallbacks for demos.

These entries keep the example command useful when a public search engine blocks automated
requests. They are still written as `needs_review` unless the verifier's confidence rules mark
them verified, and administrators should periodically re-check them.
"""

CURATED_EXAMPLES = {
    "netflix": {
        "officialWebsite": "https://www.netflix.com/fr/",
        "loginUrl": "https://www.netflix.com/login",
        "manageSubscriptionUrl": "https://www.netflix.com/YourAccount",
        "cancellationUrl": "https://help.netflix.com/en/node/407",
        "helpUrl": "https://help.netflix.com/",
        "notes": "Curated official example; Netflix cancellation help says account management may require sign-in.",
    },
    "spotify": {
        "officialWebsite": "https://www.spotify.com/fr/",
        "loginUrl": "https://accounts.spotify.com/",
        "manageSubscriptionUrl": "https://www.spotify.com/account/subscription/",
        "cancellationUrl": "https://support.spotify.com/fr/article/cancel-premium/",
        "helpUrl": "https://support.spotify.com/",
        "notes": "Curated official example for Spotify Premium cancellation support.",
    },
    "disney": {
        "officialWebsite": "https://www.disneyplus.com/fr-fr",
        "loginUrl": "https://www.disneyplus.com/login",
        "manageSubscriptionUrl": "https://www.disneyplus.com/account",
        "cancellationUrl": "https://help.disneyplus.com/article/disneyplus-en-us-cancel",
        "helpUrl": "https://help.disneyplus.com/",
        "notes": "Curated official example; third-party billed Disney+ subscriptions can require the billing partner.",
    },
    "basic-fit": {
        "officialWebsite": "https://www.basic-fit.com/fr-fr",
        "loginUrl": "https://my.basic-fit.com/login",
        "manageSubscriptionUrl": "https://my.basic-fit.com/",
        "cancellationUrl": "https://www.basic-fit.com/fr-fr/resilier/cancel-membership.html",
        "helpUrl": "https://support.basic-fit.com/",
        "notes": "Curated official France example for Basic-Fit cancellation information.",
    },
    "orange": {
        "officialWebsite": "https://www.orange.fr/",
        "loginUrl": "https://login.orange.fr/",
        "manageSubscriptionUrl": "https://espace-client.orange.fr/",
        "cancellationUrl": "https://assistance.orange.fr/article/resilier-les-etapes-pour-l-offre-internet_33762",
        "helpUrl": "https://assistance.orange.fr/",
        "notes": "Curated official France example for Orange customer-area cancellation guidance.",
    },
    "adobe": {
        "officialWebsite": "https://www.adobe.com/fr/",
        "loginUrl": "https://auth.services.adobe.com/",
        "manageSubscriptionUrl": "https://account.adobe.com/plans",
        "cancellationUrl": "https://helpx.adobe.com/manage-account/using/cancel-subscription.html",
        "helpUrl": "https://helpx.adobe.com/fr/support.html",
        "notes": "Curated official example for Adobe account plan cancellation.",
    },
}
