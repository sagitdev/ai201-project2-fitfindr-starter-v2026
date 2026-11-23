"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Criteria 1-4 each use one query run five times. Criterion 5 says "5 different
queries", so it has five scenarios, one per query. Search doesn't call the
model, so the five tries of each criterion-5 query should return the same
list. Try N in the criterion-5 row of the README is query N.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3: the id of the first search result, of
        # session["selected_item"], and of the new_item passed to
        # suggest_outfit must match. All three are printed in the trace.
        "name": "search item is the item suggest_outfit gets",
        "query": "silk slip dress in midi length under $40",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4: one listing (Platform Sneakers, $48, poshmark,
        # brand None) run five times. Checks sentence count, price, platform,
        # and that "None" never appears.
        "name": "fit card facts",
        "query": "platform sneakers size 8",
        "wardrobe": "example",
        "criterion": 4,
    },
    # Criterion 5: five different queries, each with a size and a price limit.
    # Each one is aimed at a way the size or price filter could go wrong.
    {
        # "L" must not match "XL" listings; the $26 hoodie is over the limit.
        "name": "limits: size L under $25",
        "query": "graphic tee size L under $25",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # "S" must not match shoe sizes like "US 9" ("s" is inside "us").
        "name": "limits: size S under $30",
        "query": "vintage top size S under $30",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # "M" should match "M/L"; the $75 bomber is over the limit.
        "name": "limits: size M under $50",
        "query": "jacket size M under $50",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # A half shoe size: "8.5" should match "US 8.5" and nothing else.
        "name": "limits: size 8.5 under $50",
        "query": "chelsea boots size 8.5 under $50",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # A waist size: "W30" should match "W30 L30" but not "W32" or "W28".
        "name": "limits: size W30 under $40",
        "query": "jeans size W30 under $40",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
