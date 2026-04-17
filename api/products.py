"""Vercel serverless function: return existing Hello Nancy products."""
import json
import os
from http.server import BaseHTTPRequestHandler


PRODUCTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "products.json")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
            products = json.load(f)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(products).encode("utf-8"))
