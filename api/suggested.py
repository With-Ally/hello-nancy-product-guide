"""Vercel serverless function: return saved suggestions."""
import json
import os
from http.server import BaseHTTPRequestHandler


SUGGESTED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "suggested_products.json")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if os.path.exists(SUGGESTED_PATH):
            with open(SUGGESTED_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
