"""
Hello Nancy Product Suggester
Generates product ideas via Claude API, scores them, and saves top fits.
"""

import json
import os
import sys

from score_product import score_product, load_brand_guidelines, load_products

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SUGGESTED_FILE = os.path.join(BASE_DIR, "data", "suggested_products.json")


def get_client():
    """Initialize the Anthropic client, with a clear error if key is missing."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with:  export ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)
    try:
        import anthropic
    except ImportError:
        print("ERROR: 'anthropic' package not installed.")
        print("Install it with:  pip install anthropic")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def generate_ideas(prompt, count=5):
    """Use Claude to generate product ideas based on the user's prompt."""
    client = get_client()
    guidelines = load_brand_guidelines()
    products = load_products()

    products_summary = "\n".join(
        f"- {p['name']} ({p['type']}): {p.get('features', '')}"
        for p in products
    )

    system_msg = (
        "You are a product designer for Hello Nancy, a beginner-friendly, "
        "discreet, playful self-love and education brand.\n\n"
        f"Brand guidelines:\n{guidelines}\n\n"
        f"Existing products:\n{products_summary}\n\n"
        "Generate product ideas that fit this brand. Use playful names "
        "inspired by fruits, vegetables, or cute themes. "
        "Keep descriptions beginner-friendly and non-intimidating."
    )

    user_msg = (
        f"Based on this request: '{prompt}'\n\n"
        f"Suggest exactly {count} new product ideas.\n"
        "Return ONLY a JSON array, no other text. Each item should have:\n"
        '  - "name": playful product name\n'
        '  - "type": product category (e.g. vibrator, accessory, bundle, education)\n'
        '  - "description": 1-2 sentences covering features, audience, and vibe\n'
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_msg,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()

    # Handle markdown code blocks in response
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])

    return json.loads(raw)


def suggest_and_score(prompt, count=5):
    """Generate ideas, score each one, return winners and rejected."""
    print(f"Generating {count} ideas with Claude...\n")
    ideas = generate_ideas(prompt, count)

    scored = []
    for idea in ideas:
        text = f"{idea['name']} - {idea['description']}"
        result = score_product(text)
        result["name"] = idea["name"]
        result["type"] = idea["type"]
        result["description"] = idea["description"]
        scored.append(result)

    winners = [r for r in scored if r["score"] >= 7]
    rejected = [r for r in scored if r["score"] < 7]

    # Save winners to suggested_products.json
    if winners:
        if os.path.exists(SUGGESTED_FILE):
            with open(SUGGESTED_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.extend(winners)
        with open(SUGGESTED_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

    return winners, rejected


def main():
    print("=== Hello Nancy Product Suggester ===\n")
    prompt = input("What kind of products?\n> ")
    count_input = input("How many ideas? [5]\n> ").strip()
    count = int(count_input) if count_input else 5

    winners, rejected = suggest_and_score(prompt, count)

    print(f"\n{'='*50}")
    print(f"--- ACCEPTED (score 7+) ---")
    if winners:
        for w in winners:
            print(f"\n  [{w['score']}/10] {w['name']} ({w['type']})")
            print(f"          {w['description']}")
            print(f"          Reasons:")
            for r in w.get("reasons", []):
                print(f"            - {r}")
    else:
        print("  No ideas scored 7 or above.")

    print(f"\n--- REJECTED (below 7) ---")
    if rejected:
        for r in rejected:
            print(f"  [{r['score']}/10] {r['name']} -- {r.get('reasons', [''])[0]}")
    else:
        print("  None rejected -- all ideas passed!")

    print(f"\n{len(winners)} idea(s) saved to suggested_products.json")


if __name__ == "__main__":
    main()
