import unittest

from admin_tools.cancellation_discovery.models import CancellationGuide, normalize_name
from admin_tools.cancellation_discovery.verify import verify_service


class CancellationDiscoveryTests(unittest.TestCase):
    def test_normalize_name(self):
        self.assertEqual(normalize_name("Disney+"), "disney")
        self.assertEqual(normalize_name("L'Orange Bleue"), "l-orange-bleue")

    def test_firestore_shape(self):
        guide = CancellationGuide.from_partial("Netflix", "streaming vidéo")
        data = guide.to_dict()
        self.assertEqual(data["country"], "FR")
        self.assertEqual(data["normalizedName"], "netflix")
        self.assertIn(data["status"], {"verified", "needs_review", "not_found"})

    def test_curated_example_verification(self):
        guide = verify_service("Netflix", "streaming vidéo")
        self.assertEqual(guide.normalizedName, "netflix")
        self.assertTrue(guide.cancellationUrl.startswith("https://help.netflix.com/"))
        self.assertEqual(guide.status, "verified")


if __name__ == "__main__":
    unittest.main()
