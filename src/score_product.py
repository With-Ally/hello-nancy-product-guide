"""
Hello Nancy Product-Fit Scorer
Scores a new product idea against brand guidelines and existing catalog.

Scoring logic:
  - Product type fit (is this something Hello Nancy would sell?)         0-3 pts
  - Feature fit (rechargeable, quiet, waterproof, multiple speeds, etc.) 0-3 pts
  - Vibe/aesthetic fit (cute, small, pastel, fruit-themed, etc.)         0-2 pts
  - Catalog similarity (overlaps with existing Hello Nancy products)     0-2 pts
  - Red flags (aggressive, clinical, extreme, etc.)                      -2 each
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BRAND_FILE = os.path.join(BASE_DIR, "config", "brand_guidelines.txt")
PRODUCTS_FILE = os.path.join(BASE_DIR, "data", "products.json")
SUGGESTED_FILE = os.path.join(BASE_DIR, "data", "suggested_products.json")

# --- PRODUCT TYPES that Hello Nancy sells or would sell ---
# High fit: core product categories
CORE_TYPES = [
    "vibrator", "massager", "clitoral", "wand", "bullet", "suction",
    "panty vibrator", "wearable", "egg vibrator", "mini vibe",
    "personal massager", "intimate", "self-care", "self-love",
    "pleasure", "stimulator",
]

# Medium fit: adjacent/complementary categories
ADJACENT_TYPES = [
    "lubricant", "lube", "massage oil", "massage candle",
    "storage bag", "pouch", "carrying case",
    "charger", "charging cable",
    "guide", "book", "journal", "course", "education",
    "bath bomb", "body oil", "body butter",
    "lingerie", "robe", "silk", "satin",
    "candle", "aromatherapy", "essential oil",
    "kegel", "pelvic floor",
]

# --- DESIRABLE FEATURES for Hello Nancy products ---
GOOD_FEATURES = [
    # Power & charging
    "rechargeable", "usb", "magnetic charging", "wireless",
    # User experience
    "quiet", "whisper", "silent", "waterproof", "body-safe",
    "medical grade", "body safe", "food grade",
    # Ease of use
    "one-button", "simple", "easy", "beginner", "first time",
    "multiple speeds", "adjustable", "settings", "modes", "patterns",
    "intensity", "speeds", "vibration modes",
    # Size & portability
    "mini", "compact", "portable", "small", "lightweight", "travel",
    "pocket", "discreet",
    # Materials
    "silicone", "soft touch", "smooth", "flexible",
]

# --- AESTHETIC / VIBE keywords ---
GOOD_VIBES = [
    # Colors & look
    "pastel", "pink", "soft", "cream", "minimal", "cute", "pretty",
    "clean", "elegant", "sleek", "neutral", "lavender", "purple",
    "green", "yellow", "peach", "coral",
    # Themes
    "fruit", "vegetable", "lemon", "avocado", "berry", "cherry",
    "peach", "strawberry", "flower", "floral", "bunny", "heart",
    # Vibe words
    "playful", "fun", "cheeky", "sweet", "gentle", "soothing",
    "friendly", "approachable", "cozy", "warm", "inviting",
]

# --- RED FLAGS: things Hello Nancy avoids ---
RED_FLAGS = [
    "aggressive", "clinical", "extreme", "advanced", "explicit",
    "intimidating", "medical device", "hardcore", "painful",
    "complicated", "professional-grade", "expert-level",
    "bdsm", "bondage", "restraint", "whip", "clamp",
    "realistic", "lifelike", "flesh", "skin-tone",
]


def load_brand_guidelines():
    with open(BRAND_FILE, "r", encoding="utf-8") as f:
        return f.read()


def load_products():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_suggestion(entry):
    if os.path.exists(SUGGESTED_FILE):
        with open(SUGGESTED_FILE, "r", encoding="utf-8") as f:
            suggestions = json.load(f)
    else:
        suggestions = []
    suggestions.append(entry)
    with open(SUGGESTED_FILE, "w", encoding="utf-8") as f:
        json.dump(suggestions, f, indent=2)


def check_catalog_similarity(idea_text, products):
    """Check overlap with existing Hello Nancy catalog."""
    existing_keywords = set()
    for p in products:
        for field in ["features", "name", "type"]:
            for word in p.get(field, "").lower().split():
                if len(word) > 3:
                    existing_keywords.add(word)
    matches = [kw for kw in existing_keywords if kw in idea_text]
    return matches


def score_product(idea):
    """Score a product idea against Hello Nancy brand guidelines."""
    products = load_products()
    idea_lower = idea.lower()

    score = 0.0
    reasons = []
    warning = None

    # --- 1. Product type fit (0-3 points) ---
    core_hits = [t for t in CORE_TYPES if t in idea_lower]
    adjacent_hits = [t for t in ADJACENT_TYPES if t in idea_lower]

    if core_hits:
        score += 3.0
        reasons.append(f"Core product type for Hello Nancy: {', '.join(core_hits[:3])}")
    elif adjacent_hits:
        score += 1.5
        reasons.append(f"Complementary product category: {', '.join(adjacent_hits[:3])}")

    # --- 2. Feature fit (0-3 points) ---
    feature_hits = [f for f in GOOD_FEATURES if f in idea_lower]
    if feature_hits:
        # More features = higher score, but cap at 3
        feature_score = min(len(feature_hits) * 0.6, 3.0)
        score += feature_score
        reasons.append(f"Has desirable features: {', '.join(feature_hits[:4])}")

    # --- 3. Aesthetic / vibe fit (0-2 points) ---
    vibe_hits = [v for v in GOOD_VIBES if v in idea_lower]
    if vibe_hits:
        vibe_score = min(len(vibe_hits) * 0.4, 2.0)
        score += vibe_score
        reasons.append(f"Matches Hello Nancy aesthetic: {', '.join(vibe_hits[:4])}")

    # --- 4. Catalog similarity (0-2 points) ---
    catalog_matches = check_catalog_similarity(idea_lower, products)
    if len(catalog_matches) >= 5:
        score += 2.0
        reasons.append("Strong overlap with existing Hello Nancy products")
    elif len(catalog_matches) >= 2:
        score += 1.0
        reasons.append("Some overlap with existing catalog")

    # --- 5. Red flag check (negative) ---
    flag_hits = [f for f in RED_FLAGS if f in idea_lower]
    if flag_hits:
        score -= len(flag_hits) * 2.0
        warning = f"Brand clash: {', '.join(flag_hits)}. Hello Nancy avoids these."
        reasons.append(f"WARNING: Red flags detected ({', '.join(flag_hits)})")

    # --- Baseline reason if nothing matched ---
    if not core_hits and not adjacent_hits and not feature_hits and not vibe_hits:
        reasons.append("No clear brand-fit signals found in product description")

    # Clamp score
    final_score = max(0, min(10, round(score)))

    result = {
        "idea": idea,
        "score": final_score,
        "reasons": reasons[:4],
        "warning": warning
    }

    # Auto-save if score is high enough
    if final_score >= 7:
        save_suggestion(result)

    return result


def main():
    print("=== Hello Nancy Product-Fit Scorer ===\n")
    idea = input("Describe your product idea:\n> ")

    result = score_product(idea)

    print(f"\n{'='*40}")
    print(f"Score: {result['score']}/10")
    print(f"\nReasons:")
    for r in result["reasons"]:
        print(f"  - {r}")
    if result["warning"]:
        print(f"\n[!] Warning: {result['warning']}")
    if result["score"] >= 7:
        print(f"\n[OK] Saved to suggested_products.json")
    else:
        print(f"\n[X] Score below 7 -- not saved.")


if __name__ == "__main__":
    main()
