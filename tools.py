"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""
import re
import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings



# ── Tool 1: search_listings ───────────────────────────────────────────────────
def _size_pieces(size_text:str) -> list[str]:
    pieces = re.split(r"[\s/()]+", size_text.lower())
    return [p for p in pieces if p]

def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    
    listings = load_listings()
    wanted_size = size.strip().lower() if size and size.strip() else None
    query_words = _words(description or "")

    scored = []
    for listing in listings:
        if max_price is not None:
            price = listing.get("price")
            if price is None or price > max_price:
                continue
        if wanted_size is not None:
            pieces = _size_pieces(listing.get("size") or "")
            if wanted_size not in pieces:
                continue

        listing_text = " ".join([
            listing.get("title") or "",
            listing.get("description") or "",
            " ".join(listing.get("style_tags") or []),
        ])
        score = len(query_words & _words(listing_text))
        if score == 0:
            continue
        scored.append((score, listing))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored][:config.SEARCH_RESULT_LIMIT]


    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    # TODO: replace this with your implementation

# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────
def _describe_item(item: dict) -> str:
    """Turn a listing dict into lines for a prompt, skipping empty fields."""
    lines = [f"Title: {item.get('title', 'Unknown item')}"]
    if item.get("category"):
        lines.append(f"Category: {item['category']}")
    if item.get("colors"):
        lines.append(f"Colors: {', '.join(item['colors'])}")
    if item.get("style_tags"):
        lines.append(f"Style: {', '.join(item['style_tags'])}")
    if item.get("size"):
        lines.append(f"Size: {item['size']}")
    if item.get("condition"):
        lines.append(f"Condition: {item['condition']}")
    if item.get("brand"):
        lines.append(f"Brand: {item['brand']}")
    if item.get("description"):
        lines.append(f"Description: {item['description']}")
    return "\n".join(lines)

def _format_price(price) -> str:
    """24.0 -> "$24", 24.5 -> "$24.50"."""
    if price is None:
        return "price not listed"
    if float(price).is_integer():
        return f"${int(price)}"
    return f"${price:.2f}"

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    items = (wardrobe or {}).get("items") or []
    item_text = _describe_item(new_item)

    system = (
        "You are a thrift styling assistant. You suggest outfits built around "
        "one thrifted item. Keep it short and practical."
    )

    if not items:
        prompt = (
            "The user has not entered any wardrobe items yet.\n\n"
            f"Thrifted item:\n{item_text}\n\n"
            "Start by saying in one short sentence that no wardrobe items were "
            "given. Then give general styling advice for this item: one or two "
            "outfit ideas describing the kinds of pieces that would go with it "
            "(for example 'straight-leg dark jeans'). Do not claim the user "
            "owns anything."
        )
    else:
        wardrobe_lines = []
        for piece in items:
            details = [piece.get("category") or "unknown category"]
            if piece.get("colors"):
                details.append(", ".join(piece["colors"]))
            if piece.get("style_tags"):
                details.append(", ".join(piece["style_tags"]))
            if piece.get("notes"):
                details.append(piece["notes"])
            wardrobe_lines.append(f"- {piece.get('name', 'Unnamed piece')} ({'; '.join(details)})")

        prompt = (
            f"Thrifted item:\n{item_text}\n\n"
            "The user's wardrobe:\n" + "\n".join(wardrobe_lines) + "\n\n"
            "Suggest one or two outfits. Each outfit combines the thrifted item "
            "with pieces from the wardrobe above. Name each wardrobe piece "
            "exactly as it is written in the list. Use only pieces from the "
            "list; do not invent pieces the user does not own. Add one short "
            "sentence per outfit on why it works."
        )

    text = generate(prompt, system=system)

    if not text.strip():
        return f"No outfit suggestions came back for {new_item.get('title', 'this item')}."
    return text

    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    # TODO: replace this with your implementation


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    title = new_item.get("title", "this item")

    if not outfit or not outfit.strip():
        return f"Can't write a fit card for {title}: no outfit was given."

    price_text = _format_price(new_item.get("price"))
    platform = new_item.get("platform") or "a thrift app"

    system = (
        "You write short captions people post about their thrift finds. "
        "Casual and specific, like a real post, not a product description."
    )

    prompt = (
        f"Item:\n{_describe_item(new_item)}\n\n"
        f"Outfit:\n{outfit}\n\n"
        "Write a caption of 2 to 4 sentences about this find and how it is "
        "styled. Rules:\n"
        f"- Mention the item ({title}) once.\n"
        f"- Write the price exactly as {price_text}, once.\n"
        f"- Mention the platform {platform} once.\n"
        "- Be specific about the vibe of the outfit.\n"
        "- Plain sentences only. No list of hashtags, no title line."
    )

    text = generate(prompt, system=system)

    if not text.strip():
        return f"No caption came back for {title}."
    return text

    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    # TODO: replace this with your implementation
