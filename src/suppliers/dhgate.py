"""
DHgate product search for Hello Nancy Product Guide.
Uses DuckDuckGo to find DHgate listings.
"""

import re
from ddgs import DDGS


def search_dhgate(query, max_results=12):
    """Search for products on DHgate."""
    search_query = f"site:dhgate.com/product {query}"
    try:
        raw_results = DDGS().text(search_query, max_results=max_results * 3)
    except Exception as e:
        print(f"  [DHgate] Search failed: {e}")
        return []

    products = []
    for r in raw_results:
        if len(products) >= max_results:
            break

        url = r.get("href", "")
        title = r.get("title", "")
        body = r.get("body", "")

        if not title or "dhgate.com" not in url:
            continue
        # Only keep actual product pages
        if "/product/" not in url and "/goods/" not in url:
            continue

        # Clean title
        for suffix in [" - DHgate.com", " | DHgate.com", " - dhgate.com"]:
            title = title.replace(suffix, "")

        # Extract price
        prices = re.findall(r'\$[\d,.]+(?:\s*-\s*\$?[\d,.]+)?', body)
        price = prices[0] if prices else "Contact supplier"

        # Extract MOQ
        moq_match = re.findall(r'(\d+)\s*(?:piece|pcs|unit|set)', body.lower())
        min_order = f"{moq_match[0]} pieces" if moq_match else ""

        # Extract material
        materials = re.findall(
            r'(?:silicone|abs|plastic|rubber|tpe|stainless|metal|wood|nylon|pvc)',
            body.lower(),
        )
        material = ", ".join(sorted(set(materials))).title() if materials else ""

        # Extract supplier
        supplier_match = re.search(r'//([^.]+)\.dhgate\.com', url)
        supplier = supplier_match.group(1).replace("-", " ").title() if supplier_match else "DHgate Seller"

        products.append({
            "name": title.strip(),
            "description": body[:200],
            "price": price,
            "min_order": min_order,
            "sample_price": "",
            "material": material,
            "supplier": supplier,
            "supplier_url": url,
            "url": url,
            "image": "",
            "source": "DHgate",
        })

    return products
