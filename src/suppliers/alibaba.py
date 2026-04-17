"""
Alibaba product search for Hello Nancy Product Guide.
Uses DuckDuckGo to find Alibaba listings, then fetches product pages for images and details.
"""

import re
import urllib.request
import urllib.parse
import ssl
from ddgs import DDGS


SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def search_alibaba(query, max_results=12):
    """Search Alibaba for products, return enriched results with images and details."""
    # Step 1: Find individual Alibaba product pages via DuckDuckGo
    # inurl:product-detail ensures we get specific listings, not showroom/category pages
    search_query = f"site:alibaba.com inurl:product-detail {query}"
    try:
        raw_results = DDGS().text(search_query, max_results=max_results * 3)
    except Exception as e:
        print(f"  [Alibaba] Search failed: {e}")
        return []

    # Step 2: Enrich each result with images and details from the product page
    products = []
    for r in raw_results:
        if len(products) >= max_results:
            break

        url = r.get("href", "")
        title = clean_title(r.get("title", ""))
        body = r.get("body", "")

        if not title or "alibaba.com" not in url:
            continue

        # STRICT: only keep individual product pages, reject showroom/category pages
        if "product-detail" not in url and "product-introduction" not in url:
            continue

        product = {
            "name": title,
            "description": body[:200],
            "price": extract_from_text(body, "price"),
            "min_order": extract_from_text(body, "moq"),
            "sample_price": extract_from_text(body, "sample"),
            "material": extract_from_text(body, "material"),
            "supplier": extract_supplier(url),
            "supplier_url": extract_supplier_profile(url),
            "url": url,
            "image": "",
            "source": "Alibaba",
        }

        products.append(product)

    return products


def fetch_product_details(url):
    """Fetch an Alibaba product page and extract image, price, MOQ, material."""
    details = {}
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return details

    # Extract product image from alicdn
    img_patterns = [
        r'(https?://s\.alicdn\.com/@sc\d+/kf/[^"\'>\s\\]+\.(?:jpg|png|webp))',
        r'(https?://cbu\d*\.alicdn\.com/[^"\'>\s\\]+\.(?:jpg|png|webp))',
        r'(https?://i\d*\.alicdn\.com/[^"\'>\s\\]+\.(?:jpg|png|webp))',
    ]
    for pattern in img_patterns:
        imgs = re.findall(pattern, html)
        # Filter out tiny icons and logos
        product_imgs = [i for i in imgs if "logo" not in i.lower() and "icon" not in i.lower()]
        if product_imgs:
            details["image"] = product_imgs[0]
            break

    # Extract price
    price_match = re.search(r'US\s*\$\s*([\d.]+(?:\s*-\s*\$?\s*[\d.]+)?)', html)
    if price_match:
        details["price"] = f"${price_match.group(1).strip()}"

    # Extract MOQ
    moq_match = re.search(r'(\d+)\s*(?:Piece|piece|pcs|PCS|Unit|unit|Set|set)\s*(?:\(MOQ\)|Min)', html, re.IGNORECASE)
    if moq_match:
        details["min_order"] = f"{moq_match.group(1)} pieces"

    # Extract material
    mat_match = re.search(r'(?:Material|material)[:\s]*([A-Za-z][A-Za-z\s,/+]+?)(?:[<\n|])', html)
    if mat_match:
        details["material"] = mat_match.group(1).strip()[:50]

    # Extract sample price
    sample_match = re.search(r'[Ss]ample\s*[Pp]rice[:\s]*\$?([\d.]+)', html)
    if sample_match:
        details["sample_price"] = f"${sample_match.group(1)}"

    # Extract supplier name
    supplier_match = re.search(r'"companyName":"([^"]+)"', html)
    if supplier_match:
        details["supplier"] = supplier_match.group(1)

    return details


def clean_title(title):
    """Clean product title."""
    for suffix in [" - Alibaba.com", " | Alibaba.com", " - alibaba.com"]:
        title = title.replace(suffix, "")
    return title.strip()


def extract_from_text(text, field):
    """Extract structured info from search result body text."""
    text_lower = text.lower()

    if field == "price":
        prices = re.findall(r'\$[\d,.]+(?:\s*-\s*\$?[\d,.]+)?', text)
        return prices[0] if prices else "Contact supplier"

    if field == "moq":
        moq = re.findall(r'(\d+)\s*(?:piece|pcs|unit|set)', text_lower)
        return f"{moq[0]} pieces" if moq else ""

    if field == "material":
        materials = re.findall(
            r'(?:silicone|abs|plastic|rubber|tpe|stainless|metal|wood|nylon|pvc|latex)',
            text_lower,
        )
        return ", ".join(sorted(set(materials))).title() if materials else ""

    if field == "sample":
        sample = re.search(r'sample\s*(?:price)?[:\s]*\$?([\d.]+)', text_lower)
        return f"${sample.group(1)}" if sample else ""

    return ""


def extract_supplier(url):
    """Extract supplier name from URL."""
    match = re.search(r'//([^.]+)\.en\.alibaba', url)
    if match:
        return match.group(1).replace("-", " ").title()
    return "Alibaba Supplier"


def extract_supplier_profile(url):
    """Extract supplier profile URL."""
    match = re.search(r'(https?://[^.]+\.en\.alibaba\.com)', url)
    if match:
        return match.group(1)
    match = re.search(r'//([^/]+alibaba\.com)', url)
    if match:
        return f"https://{match.group(1)}"
    return "https://www.alibaba.com"
