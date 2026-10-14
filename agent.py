"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card, _size_pieces
from generate import ModelUnavailable
from utils.data_loader import load_listings


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }

# ── query parsing ─────────────────────────────────────────────────────────────

# Size words a user might type after "size", mapped to the letters in the data.
_SIZE_WORDS = {
    "extra small": "xs",
    "small": "s",
    "medium": "m",
    "large": "l",
    "extra large": "xl",
}

# Common words that describe the request, not the item. Removed from the
# description so they don't add points for matching unrelated listings.
_FILLER_WORDS = {
    "a", "an", "the", "i", "im", "want", "need", "looking", "look", "for",
    "find", "me", "some", "something", "in", "with", "and", "or", "of", "to",
    "please", "under", "below", "less", "than", "max", "up", "around",
    "size", "dollars", "dollar", "usd", "bucks",
}

_NUMBER = r"(\d+(?:\.\d+)?)"


def _cut(text: str, match: re.Match) -> str:
    """Remove the matched part of the text, so it doesn't end up in the description."""
    return text[: match.start()] + " " + text[match.end():]


def _parse_query(query: str) -> dict:
    """
    Pull a description, a size, and a max_price out of a plain-language query,
    using regular expressions.

    "vintage graphic tee under $30, size M"
        -> {"description": "vintage graphic tee", "size": "m", "max_price": 30.0}
    """
    text = (query or "").lower()
    max_price = None
    size = None

    # 1. A price range like "$30-$40" or "30 to 40 dollars": use the upper bound,
    #    because search_listings only takes a max_price.
    range_match = (
        re.search(rf"\$\s*{_NUMBER}\s*(?:-|to)\s*\$?\s*{_NUMBER}", text)
        or re.search(rf"{_NUMBER}\s*(?:-|to)\s*{_NUMBER}\s*(?:dollars?|usd|bucks)", text)
    )
    if range_match:
        max_price = max(float(range_match.group(1)), float(range_match.group(2)))
        text = _cut(text, range_match)
    else:
        # 2. A single price: "$30", "under 30", "30 dollars".
        price_match = (
            re.search(rf"\$\s*{_NUMBER}", text)
            or re.search(rf"(?:under|below|less than|up to|max)\s+{_NUMBER}", text)
            or re.search(rf"{_NUMBER}\s*(?:dollars?|usd|bucks)", text)
        )
        if price_match:
            max_price = float(price_match.group(1))
            text = _cut(text, price_match)

    # 3. A size, only when it follows the word "size":
    #    "size M", "size 8.5", "size US 8", "size S/M", "size medium".
    size_match = re.search(
        r"\bsize\s+(?:us\s+)?(extra small|extra large|[a-z0-9]+(?:\.\d+)?(?:/[a-z0-9]+)?)\b",
        text,
    )
    if size_match:
        raw_size = size_match.group(1)
        size = _SIZE_WORDS.get(raw_size, raw_size)
        text = _cut(text, size_match)

    # 4. Whatever is left, minus filler words, is the description.
    words = re.findall(r"[a-z0-9]+", text)
    description = " ".join(w for w in words if w not in _FILLER_WORDS)

    return {"description": description, "size": size, "max_price": max_price}


def _price_text(price: float) -> str:
    """5.0 -> "$5", 8.5 -> "$8.5"."""
    return f"${price:g}"

def _count_within_limits(size: str | None, max_price: float | None) -> int:
    """
    How many listings, of any kind, fit the size and price limit alone.

    Uses the same size rule as search_listings, so the count matches what a
    search would let through.
    """
    count = 0
    for listing in load_listings():
        if max_price is not None:
            price = listing.get("price")
            if price is None or price > max_price:
                continue
        if size and size not in _size_pieces(listing.get("size") or ""):
            continue
        count += 1
    return count

def _no_results_message(parsed: dict) -> str:
    """
    Explain an empty search in a way the user can act on.

    Re-runs search_listings with one filter removed at a time, to find out
    which filter is in the way. search_listings is plain code, so these extra
    searches are fast and use no model calls.
    """
    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    if not description:
        return (
            "I couldn't tell what item you're looking for. Add a word for the "
            "item itself, like 'graphic tee', 'jeans', or 'denim jacket'."
        )

    searched = f"No listings matched '{description}'"
    if size:
        searched += f" in size {size.upper()}"
    if max_price is not None:
        searched += f" at or under {_price_text(max_price)}"

    tips = []
    if max_price is not None and search_listings(description, size, None):
        tips.append(f"raise your price limit above {_price_text(max_price)} (there are matches at higher prices)")
    if size and search_listings(description, None, max_price):
        tips.append(f"remove the size {size.upper()} (there are matches in other sizes)")

    if not tips:
        if (size or max_price is not None) and search_listings(description, None, None):
            tips.append("remove both the size and the price limit (there are matches without them)")
        else:
            tip = (
                f"describe the item with different or fewer words, since nothing in "
                f"the listings matches '{description}' at any size or price. "
                f"A general word like 'tee', 'jeans', 'jacket', or 'dress' is a good start"
            )

            if size or max_price is not None:
                limits = []
                if size:
                    limits.append(f"in size {size.upper()}")
                if max_price is not None:
                    limits.append(f"at or under {_price_text(max_price)}")
                limits_text = " ".join(limits)

                count = _count_within_limits(size, max_price)
                if count == 0:
                    tip += (
                        f". Your other limits are too tight as well: no listing of "
                        f"any kind is {limits_text}, so loosen those too"
                    )
                else:
                    tip += (
                        f". Your other limits are fine: {count} listings are "
                        f"{limits_text}"
                    )

            tips.append(tip)

    return f"{searched}. To find something, {' or '.join(tips)}."

# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    next_step = "parse"
    count = 0

    while next_step != "done":
        count += 1
        trace.check_iterations(count)

        if next_step == "parse":
            session["parsed"] = _parse_query(query)
            next_step = "search"

        elif next_step == "search":
            parsed = session["parsed"]
            session["search_results"] = search_listings(
                parsed["description"], parsed["size"], parsed["max_price"]
            )

            # THE BRANCH: decided by what search_listings just returned.
            if not session["search_results"]:
                session["error"] = _no_results_message(parsed)
                next_step = "done"
            else:
                next_step = "select"

        elif next_step == "select":
            session["selected_item"] = session["search_results"][0]
            next_step = "suggest"

        elif next_step == "suggest":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            next_step = "card"

        elif next_step == "card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            next_step = "done"

        else:
            session["error"] = f"Internal error: unknown step '{next_step}'."
            next_step = "done"

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
