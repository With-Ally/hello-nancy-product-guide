"""
Hello Nancy AI-Powered Product Scorer
Uses Claude to intelligently score products against brand guidelines.
Falls back to keyword scorer if API is unavailable.
"""

import json
import os
import re

import anthropic

from score_product import (
    load_brand_guidelines,
    load_products,
    score_product as keyword_score_product,
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def _build_system_prompt():
    """Build the system prompt with brand guidelines and existing catalog."""
    guidelines = load_brand_guidelines()
    products = load_products()

    catalog = "\n".join(
        f"- {p['name']} ({p['type']}): {p.get('features', '')} | Vibe: {p.get('vibe', '')}"
        for p in products
    )

    return f"""You are the brand-fit evaluator for Hello Nancy, an intimate self-love brand.

{guidelines}

EXISTING PRODUCT CATALOG:
{catalog}

YOUR JOB:
Score how well a product idea fits the Hello Nancy brand on a scale of 0-10.

SCORING CRITERIA:
- Product type fit: Is this something Hello Nancy would sell? (vibrators, massagers, accessories, education, self-care) → 0-3 pts
- Feature fit: Does it have desirable features? (rechargeable, silicone, waterproof, quiet, multiple speeds, compact, body-safe) → 0-3 pts
- Aesthetic/vibe fit: Does it match Hello Nancy's playful, cute, pastel, fruit/veggie-themed look? → 0-2 pts
- Catalog fit: Would it sit naturally alongside existing products? → 0-2 pts
- Red flags: Subtract points for anything aggressive, clinical, intimidating, explicit, BDSM, realistic/lifelike

IMPORTANT:
- Hello Nancy is specifically an ADULT INTIMATE PRODUCTS brand. Products that are NOT adult/intimate (face massagers, kitchen items, etc.) should score 0.
- A product doesn't need to use Hello Nancy's exact brand words to score well. Use your judgment — a "mini pink silicone wand with USB charging" is obviously a great fit even if it doesn't say "beginner-friendly".
- Be practical: supplier listings use factory/wholesale language, not marketing language. Evaluate the PRODUCT, not the listing copy.

RESPOND WITH ONLY valid JSON, no markdown, no code blocks:
{{"score": <0-10>, "reasons": ["reason 1", "reason 2", "reason 3"], "warning": "<warning text or null>"}}"""


def ai_score_product(idea):
    """Score a product idea using Claude AI."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return keyword_score_product(idea)

    try:
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=_build_system_prompt(),
            messages=[
                {
                    "role": "user",
                    "content": f"Score this product for Hello Nancy:\n\n{idea}",
                }
            ],
        )

        raw = response.content[0].text.strip()

        # Handle markdown code blocks just in case
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])

        result = json.loads(raw)

        # Validate the response has required fields
        result.setdefault("score", 0)
        result.setdefault("reasons", [])
        result.setdefault("warning", None)
        result["idea"] = idea
        result["scorer"] = "ai"

        # Clamp score
        result["score"] = max(0, min(10, int(result["score"])))

        return result

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"  [AI Scorer] Parse error, falling back to keywords: {e}")
        return keyword_score_product(idea)
    except anthropic.APIError as e:
        print(f"  [AI Scorer] API error, falling back to keywords: {e}")
        return keyword_score_product(idea)
    except Exception as e:
        print(f"  [AI Scorer] Unexpected error, falling back to keywords: {e}")
        return keyword_score_product(idea)
