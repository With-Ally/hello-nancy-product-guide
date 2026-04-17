"""
Taobao / 1688 product search for Hello Nancy Product Guide.
Uses DuckDuckGo to find Taobao and 1688 (Alibaba China) listings.
"""

import re
from ddgs import DDGS


def _safe_print(msg):
    """Print with encoding safety for Windows."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))


def search_taobao(query, max_results=12):
    """Search for products on Taobao."""
    search_query = f"site:taobao.com {query}"
    try:
        raw_results = DDGS().text(search_query, max_results=max_results * 2)
    except Exception as e:
        _safe_print(f"  [Taobao] Search failed: {e}")
        return []

    return _parse_results(raw_results, "Taobao", "taobao.com", max_results)


def search_1688(query, max_results=12):
    """Search for products on 1688 (Alibaba China wholesale)."""
    search_query = f"site:1688.com {query}"
    try:
        raw_results = DDGS().text(search_query, max_results=max_results * 2)
    except Exception as e:
        _safe_print(f"  [1688] Search failed: {e}")
        return []

    return _parse_results(raw_results, "1688", "1688.com", max_results)


def _parse_results(raw_results, source, domain, max_results):
    """Parse search results into product dicts."""
    products = []
    for r in raw_results:
        if len(products) >= max_results:
            break

        url = r.get("href", "")
        title = r.get("title", "").encode("ascii", errors="replace").decode("ascii")
        body = r.get("body", "").encode("ascii", errors="replace").decode("ascii")

        if not title or domain not in url:
            continue

        # Clean title
        for suffix in [f" - {source}", f" | {source}", " - Taobao", " - 1688.com"]:
            title = title.replace(suffix, "")

        # Extract price (CNY or USD)
        cny_prices = re.findall(r'[\u00a5\uffe5]?\s*(\d+(?:\.\d{2})?)', body)
        usd_prices = re.findall(r'\$[\d,.]+', body)
        if usd_prices:
            price = usd_prices[0]
        elif cny_prices:
            price = f"\u00a5{cny_prices[0]}"
        else:
            price = "Contact supplier"

        # Extract MOQ
        moq_match = re.findall(r'(\d+)\s*(?:piece|pcs|unit|set|\u4ef6|\u4e2a)', body.lower())
        min_order = f"{moq_match[0]} pieces" if moq_match else ""

        # Extract material
        materials = re.findall(
            r'(?:silicone|abs|plastic|rubber|tpe|stainless|metal|wood|nylon)',
            body.lower(),
        )
        material = ", ".join(sorted(set(materials))).title() if materials else ""

        # Supplier
        supplier_match = re.search(r'//([^.]+)\.' + re.escape(domain), url)
        supplier = supplier_match.group(1).replace("-", " ").title() if supplier_match else f"{source} Seller"

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
            "source": source,
        })

    return products
