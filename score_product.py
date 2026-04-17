"""
Hello Nancy Product-Fit Scorer
Reads brand guidelines and existing products, scores a new product idea.
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BRAND_FILE = os.path.join(os.path.dirname(__file__), "brand_guidelines.txt")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
SUGGESTED_FILE = os.path.join(DATA_DIR, "suggested_products.json")


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


def score_product_idea(idea_name, idea_description):
    """Stub: replace with scoring logic (or Claude API call) in next step."""
    # TODO: implement scoring against brand guidelines
    return {
        "name": idea_name,
        "description": idea_description,
        "score": 0,
        "explanation": "Scoring not yet implemented."
    }


def main():
    print("=== Hello Nancy Product-Fit Scorer ===\n")
    idea_name = input("Product idea name: ")
    idea_description = input("Brief description: ")

    result = score_product_idea(idea_name, idea_description)

    print(f"\nScore: {result['score']}/10")
    print(f"Explanation: {result['explanation']}")

    if result["score"] >= 7:
        save_suggestion(result)
        print(">> Saved to suggested_products.json")
    else:
        print(">> Score below 7, not saved.")


if __name__ == "__main__":
    main()
