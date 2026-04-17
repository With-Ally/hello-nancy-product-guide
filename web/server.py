"""
Hello Nancy Product Guide — Web Server
Serves the dashboard and connects it to the scoring engine + supplier search.
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add src/ to path so we can import modules
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from score_product import load_products
from ai_scorer import ai_score_product
from suppliers.search import search_and_score

WEB_DIR = os.path.dirname(__file__)
SUGGESTED_FILE = os.path.join(BASE_DIR, "data", "suggested_products.json")


class DashboardHandler(SimpleHTTPRequestHandler):
    """Handles static files, scoring API, and supplier search API."""

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, directory=WEB_DIR, **kwargs)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/products":
            self._send_json(load_products())
        elif parsed.path == "/suggested":
            self._send_json(self._load_suggested())
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if parsed.path == "/score":
            idea = body.get("idea", "")
            result = ai_score_product(idea)
            self._send_json(result)

        elif parsed.path == "/search":
            query = body.get("query", "")
            max_results = body.get("max_results", 12)
            print(f"\n[Search] Query: {query}")
            results = search_and_score(query, max_results)
            print(f"[Search] Returned {len(results)} scored results")
            self._send_json(results)

        elif parsed.path == "/save":
            product = body.get("product", {})
            self._save_suggestion(product)
            self._send_json({"status": "saved"})

        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _send_json(self, data):
        try:
            payload = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(payload)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _load_suggested(self):
        if os.path.exists(SUGGESTED_FILE):
            with open(SUGGESTED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_suggestion(self, product):
        suggestions = self._load_suggested()
        suggestions.append(product)
        with open(SUGGESTED_FILE, "w", encoding="utf-8") as f:
            json.dump(suggestions, f, indent=2)

    def log_message(self, format, *args):
        print(f"  {args[0]}")


def main():
    port = 5000
    server = HTTPServer(("localhost", port), DashboardHandler)
    print(f"=== Hello Nancy Product Guide ===")
    print(f"Dashboard running at: http://localhost:{port}")
    print(f"Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
