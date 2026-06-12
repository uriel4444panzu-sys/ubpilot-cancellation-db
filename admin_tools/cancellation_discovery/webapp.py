"""Local web interface for the admin cancellation-discovery tool.

This serves a single-page admin UI using only the Python standard library (no Flask/Django).
It wraps the existing discovery, verification and export logic so an administrator can work
with a real interface instead of the command line.

Safety: like the CLI, the server only reads public URLs and search results. It never logs in,
solves captchas, or bypasses paywalls. It is meant to run locally for a single administrator
and binds to 127.0.0.1 by default.
"""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .categories import CATEGORIES
from .discover import discover_category
from .models import CancellationGuide
from .verify import guides_to_csv_str, guides_to_json_str, verify_service

INDEX_HTML = Path(__file__).resolve().parent / "web" / "index.html"


def _guides_payload(guides: list[CancellationGuide]) -> list[dict]:
    return [guide.to_dict() for guide in guides]


class AdminRequestHandler(BaseHTTPRequestHandler):
    server_version = "SubPilotAdminUI/0.1"

    # --- helpers -------------------------------------------------------
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def log_message(self, fmt: str, *args) -> None:  # quieter console
        return

    # --- routing -------------------------------------------------------
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            try:
                body = INDEX_HTML.read_bytes()
            except FileNotFoundError:
                self._send(500, b"index.html missing", "text/plain; charset=utf-8")
                return
            self._send(200, body, "text/html; charset=utf-8")
        elif self.path == "/api/categories":
            self._send_json({"categories": [{"key": key, "label": label} for key, label in sorted(CATEGORIES.items())]})
        else:
            self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        try:
            handler = {
                "/api/discover": self._handle_discover,
                "/api/verify": self._handle_verify,
                "/api/export": self._handle_export,
                "/api/firestore": self._handle_firestore,
                "/api/firestore-list": self._handle_firestore_list,
            }.get(self.path)
            if handler is None:
                self._send(404, b"Not found", "text/plain; charset=utf-8")
                return
            handler(self._read_json())
        except Exception as exc:  # surface errors to the UI instead of crashing
            self._send_json({"error": str(exc)}, status=400)

    # --- endpoints -----------------------------------------------------
    def _handle_discover(self, data: dict) -> None:
        keys = data.get("categories") or []
        if not keys:
            raise ValueError("Sélectionne au moins une catégorie.")
        limit = int(data.get("limitPerQuery", 8))
        include_seeds = bool(data.get("includeSeeds", True))
        guides: list[CancellationGuide] = []
        for key in keys:
            guides.extend(discover_category(key, limit_per_query=limit, include_seeds=include_seeds))
        self._send_json({"guides": _guides_payload(guides)})

    def _handle_verify(self, data: dict) -> None:
        services = data.get("services") or []
        if not services:
            raise ValueError("Aucun service à vérifier.")
        country = data.get("country") or "FR"
        guides: list[CancellationGuide] = []
        for item in services:
            if item.get("verifiedManually"):
                # Admin-certified row: keep everything as entered, never re-search or overwrite.
                guide = CancellationGuide.from_dict(item)
                guide.verifiedManually = True
                guide.status = "verified"
                guides.append(guide)
                continue
            guides.append(
                verify_service(
                    item["serviceName"],
                    item.get("category", "needs_review"),
                    official_website=item.get("officialWebsite", ""),
                    country=country,
                    login_url=item.get("loginUrl", ""),
                    manage_subscription_url=item.get("manageSubscriptionUrl", ""),
                    cancellation_url=item.get("cancellationUrl", ""),
                    help_url=item.get("helpUrl", ""),
                )
            )
        self._send_json({"guides": _guides_payload(guides)})

    def _handle_export(self, data: dict) -> None:
        guides = [CancellationGuide.from_dict(item) for item in data.get("guides") or []]
        fmt = (data.get("format") or "json").lower()
        if fmt == "csv":
            content = guides_to_csv_str(guides)
        else:
            content = guides_to_json_str(guides)
        self._send_json({"format": fmt, "content": content, "count": len(guides)})

    def _handle_firestore(self, data: dict) -> None:
        guides = [CancellationGuide.from_dict(item) for item in data.get("guides") or []]
        if not guides:
            raise ValueError("Aucun guide à écrire.")
        from .firestore_writer import write_guides

        write_guides(guides, project_id=data.get("projectId") or None)
        self._send_json({"written": len(guides)})

    def _handle_firestore_list(self, data: dict) -> None:
        from .firestore_writer import read_guides

        documents = read_guides(project_id=data.get("projectId") or None)
        self._send_json({"guides": documents, "count": len(documents)})


def run(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:
    if not INDEX_HTML.exists():
        raise FileNotFoundError(f"UI template introuvable: {INDEX_HTML}")
    httpd = ThreadingHTTPServer((host, port), AdminRequestHandler)
    url = f"http://{host}:{port}/"
    print(f"Interface admin SubPilot démarrée sur {url}")
    print("Ctrl+C pour arrêter.")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt de l'interface.")
    finally:
        httpd.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Interface web locale pour l'outil admin de découverte/résiliation.")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute (défaut: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Port d'écoute (défaut: 8000).")
    parser.add_argument("--no-browser", action="store_true", help="Ne pas ouvrir le navigateur automatiquement.")
    args = parser.parse_args()
    run(host=args.host, port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
