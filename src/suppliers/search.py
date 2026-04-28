"""
Unified supplier search — searches across Alibaba, DHgate, Taobao, and 1688,
then scores results against Hello Nancy brand guidelines.

All searches are scoped to adult intimate / sex toy products to match
Hello Nancy's product category.
"""

import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from suppliers.alibaba import search_alibaba
from suppliers.dhgate import search_dhgate
from ai_scorer import ai_score_product

# Only suppliers with public product pages (no login/captcha walls)
SUPPLIERS = {
    "Alibaba": search_alibaba,
    "DHgate": search_dhgate,
}

# Shorter context — just enough to steer results without overloading the query
PRODUCT_CONTEXT = "vibrator adult toy"

# A product MUST contain at least one of these to be kept.
# If none match, it gets dropped — no exceptions.
MUST_MATCH = [
    # Core product types
    "vibrator", "vibrating", "vibe", "bullet",
    "dildo", "sex toy", "adult toy",
    "clitoral", "clit", "g-spot", "g spot",
    "stimulator", "stimulation",
    "wand massager", "personal massager", "massager women",
    "panty vibrator", "wearable vibrator", "love egg", "vibrating egg",
    "suction toy", "air pulse", "air suction",
    "kegel", "pelvic floor", "ben wa",
    # Adjacent products Hello Nancy might sell
    "lubricant", "lube", "intimate gel", "massage oil",
    # Category signals
    "intimate", "erotic", "orgasm", "foreplay",
    "self-love", "self-pleasure", "pleasure toy",
    "sex", "adult", "sensual",
]


def enrich_query(user_query):
    """Always add adult product context to keep results in category."""
    return f"{user_query} {PRODUCT_CONTEXT}"


def is_relevant(product):
    """Only keep products that are clearly adult intimate products."""
    text = f"{product.get('name', '')} {product.get('description', '')}".lower()

    # Must contain at least one adult/intimate product signal
    if any(signal in text for signal in MUST_MATCH):
        return True

    # No adult product signal found — drop it
    return False


def has_valid_product_url(product):
    """Check if URL pattern looks like a real product page (no HTTP requests)."""
    url = product.get("url", "")
    if not url:
        return False
    # Alibaba: must be product-detail or product-introduction
    if "alibaba.com" in url:
        return "product-detail" in url or "product-introduction" in url
    # DHgate: must be /product/ or /goods/
    if "dhgate.com" in url:
        return "/product/" in url or "/goods/" in url
    # Other: just needs to be a real URL
    return url.startswith("http")


def search_and_score(query, max_results=12):
    """
    Search all suppliers in parallel, score each product against brand guidelines.
    Returns results sorted by brand-fit score (highest first).
    """
    enriched_query = enrich_query(query)
    per_supplier = max(5, max_results // len(SUPPLIERS))
    all_results = []

    # Search all suppliers in parallel
    print(f"  Searching {len(SUPPLIERS)} suppliers for: {enriched_query}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(fn, enriched_query, per_supplier): name
            for name, fn in SUPPLIERS.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results = future.result()
                print(f"  [{name}] Found {len(results)} results")
                all_results.extend(results)
            except Exception as e:
                print(f"  [{name}] Error: {e}")

    # Filter out non-relevant products (facial massagers, massage guns, etc.)
    relevant = [p for p in all_results if is_relevant(p)]
    dropped = len(all_results) - len(relevant)
    if dropped:
        print(f"  Filtered out {dropped} non-relevant results")

    # Filter by URL pattern — only keep real product page URLs
    live = [p for p in relevant if has_valid_product_url(p)]
    url_dropped = len(relevant) - len(live)
    if url_dropped:
        print(f"  Dropped {url_dropped} non-product URLs")

    # Score each result against brand guidelines using AI (in parallel)
    def score_one(product):
        text = f"{product['name']} {product.get('description', '')}"
        result = ai_score_product(text)
        product["score"] = result["score"]
        product["reasons"] = result["reasons"]
        product["warning"] = result["warning"]
        return product

    scored = []
    if live:
        with ThreadPoolExecutor(max_workers=min(8, len(live))) as pool:
            scored = list(pool.map(score_one, live))

    # Sort by score descending, then by source
    scored.sort(key=lambda x: (-x["score"], x["source"]))

    return scored[:max_results]
