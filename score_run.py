#!/usr/bin/env python3
"""
Score a run log from run_eval.py against criteria.md.  ← UNIT 4, MILESTONE 3

    python score_run.py results/run_<stamp>_before.md

run_eval.py runs the scenarios and leaves the PASS/FAIL cells blank. This
script fills them in by applying each criterion in criteria.md exactly as
written, and prints the reason for every cell so a reader can check it.

It reads only the run log, except for criterion 5. The run log shows how many
listings search returned but not every listing's size and price, so for
criterion 5 this script searches again through MCP, the same path the agent
uses. Search does not call the model, so the result is the same list. It then
checks that the count and first title match what the run log recorded.

This script doesn't run the agent or call the model.
"""

import re
import sys
from pathlib import Path

import scenarios as scenario_module

TARGETS = {1: 4, 2: 5, 3: 5, 4: 4, 5: 5}
TITLES = {
    1: "1. Matching query completes all three tools",
    2: "2. Impossible query stops before suggest_outfit",
    3: "3. Search item = selected_item = suggest_outfit's new_item (by id)",
    4: "4. Fit card: 2-4 sentences, price, platform, no 'None'",
    5: "5. Search respects size and price limits (5 queries)",
}
BLOCK_LABELS = {"Outfit suggestion:": "outfit", "Fit card:": "fit_card",
                "Trace:": "trace", "Crashed:": "crashed"}


# ── reading the run log ───────────────────────────────────────────────────────

def parse_log(text: str) -> dict[str, list[dict]]:
    """{scenario name: [try dict, ...]} from run_eval.py's markdown."""
    body = text.split("## What actually happened", 1)[1]
    runs: dict[str, list[dict]] = {}
    for section in re.split(r"^### ", body, flags=re.M)[1:]:
        name, _, rest = section.partition("\n")
        tries = []
        for chunk in re.split(r"^\*\*Try \d+\*\*$", rest, flags=re.M)[1:]:
            tries.append(_parse_try(chunk))
        runs[name.strip()] = tries
    return runs


def _parse_try(chunk: str) -> dict:
    record = {"stopped": None, "error": "", "item_title": None, "item_price": None,
              "item_platform": None, "result_count": None, "outfit": None,
              "fit_card": None, "trace": "", "crashed": None}
    lines = chunk.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("- stopped early: "):
            value = line[len("- stopped early: "):]
            record["stopped"] = value.startswith("yes")
            record["error"] = value.split("— ", 1)[1] if "— " in value else ""
        elif line.startswith("- selected_item: "):
            value = line[len("- selected_item: "):]
            m = re.match(r"(.*) \(\$([\d.]+), (\S+)\)$", value)
            if m:
                record["item_title"] = m.group(1)
                record["item_price"] = float(m.group(2))
                record["item_platform"] = m.group(3)
        elif line.startswith("- search_results: "):
            record["result_count"] = int(line.split(": ", 1)[1])
        elif line.strip() in BLOCK_LABELS:
            key = BLOCK_LABELS[line.strip()]
            j = i + 1
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            k = j + 1
            while k < len(lines) and lines[k].strip() != "```":
                k += 1
            record[key] = "\n".join(lines[j + 1:k])
            i = k
        i += 1
    return record


def _trace_steps(trace: str) -> list[str]:
    return re.findall(r"^\[\d+\] (.+)$", trace, flags=re.M)


# ── the five criteria, as written in criteria.md ──────────────────────────────

FALLBACK_CARDS = ("No caption came back", "Can't write a fit card")


def check_1(t: dict) -> tuple[bool, str]:
    if t["crashed"]:
        return False, f"crashed: {t['crashed']}"
    if t["stopped"]:
        return False, f"stopped early: {t['error'][:80]}"
    steps = _trace_steps(t["trace"])
    missing = [s for s in ("search_listings (via MCP)", "suggest_outfit", "create_fit_card")
               if s not in steps]
    if missing:
        return False, f"trace is missing {', '.join(missing)}"
    card = (t["fit_card"] or "").strip()
    if not card or card.startswith(FALLBACK_CARDS):
        return False, f"no usable fit card: {card[:60]!r}"
    return True, f"all three tools ran; fit card {len(card)} chars"


ACTION_WORDS = ("raise", "remove", "describe", "loosen", "add", "try", "change")


def check_2(t: dict) -> tuple[bool, str]:
    if t["crashed"]:
        return False, f"crashed: {t['crashed']}"
    if not t["stopped"]:
        return False, "did not stop"
    steps = _trace_steps(t["trace"])
    if "suggest_outfit" in steps or "create_fit_card" in steps:
        return False, f"stopped, but trace shows {steps}"
    message = t["error"]
    if not any(word in message.lower() for word in ACTION_WORDS):
        return False, f"message names nothing to change: {message[:80]!r}"
    return True, f"stopped after {steps[-1]}; message says what to change"


def check_3(t: dict) -> tuple[bool, str]:
    if t["crashed"]:
        return False, f"crashed: {t['crashed']}"
    trace = t["trace"]
    first = re.search(r"\(first id (\S+)\)", trace)
    selected = re.search(r"best match \(id (\S+)\)", trace)
    passed = re.search(r"^\[\d+\] suggest_outfit\n\s+in:\s+new_item=(\S+) ", trace, flags=re.M)
    ids = {"search[0]": first and first.group(1),
           "selected_item": selected and selected.group(1),
           "suggest_outfit new_item": passed and passed.group(1)}
    if None in ids.values():
        missing = [k for k, v in ids.items() if v is None]
        return False, f"trace has no id for {', '.join(missing)}"
    if len(set(ids.values())) != 1:
        return False, "ids differ: " + ", ".join(f"{k}={v}" for k, v in ids.items())
    return True, f"all three ids are {ids['selected_item']}"


def _sentences(text: str) -> int:
    """Pieces ending in . ! or ? (followed by a space or the end) that contain a letter.
    A final piece with no end mark still counts as a sentence."""
    pieces = re.split(r"[.!?]+(?=\s|$)", text.strip())
    return sum(1 for piece in pieces if re.search(r"[A-Za-z]", piece))


def _price_pattern(price: float) -> str:
    whole = f"{price:.2f}"
    if price.is_integer():
        return rf"\${int(price)}(?:\.00)?(?!\.?\d)"
    return rf"\${re.escape(whole)}(?!\d)"


def check_4(t: dict) -> tuple[bool, str]:
    if t["crashed"]:
        return False, f"crashed: {t['crashed']}"
    card = (t["fit_card"] or "").strip()
    if not card:
        return False, "no fit card"
    problems = []
    n = _sentences(card)
    if not 2 <= n <= 4:
        problems.append(f"{n} sentences")
    if not re.search(_price_pattern(t["item_price"]), card):
        problems.append(f"no ${t['item_price']:g} price")
    if t["item_platform"].lower() not in card.lower():
        problems.append(f"no platform '{t['item_platform']}'")
    if re.search(r"\bNone\b", card):
        problems.append("contains 'None'")
    if problems:
        return False, "; ".join(problems)
    return True, f"{n} sentences, ${t['item_price']:g}, {t['item_platform']}, no 'None'"


# Revised criterion 4 (unit 4, see criteria.md): the card must also present the
# item as BOUGHT on the listing's platform. These patterns catch the two ways
# the before run got that wrong. Checked by hand against all 45 before-run
# cards: they flag the same 20 cards I flagged reading them.
SELLING = re.compile(
    r"cross-?list|\blist(?:ed|ing)?\b|went live|"
    r"live (?:now )?on my (?:depop|poshmark|thredup|closet|shop)|"
    r"dropped (?:them|it) (?:over )?on|on my (?:depop|poshmark|thredup|shop)|"
    r"my shop|posting it on|up for \$|keeping it on",
    re.I,
)
OTHER_SOURCE = re.compile(
    r"estate sale|thrifting|thrift store|flea market|\bbins\b|garage sale|yard sale", re.I
)


def platform_role_problems(card: str) -> list[str]:
    """Ways the card misstates where the item came from. Empty list = fine."""
    problems = []
    if m := SELLING.search(card):
        problems.append(f"says the user is selling it ({m.group(0)!r})")
    if m := OTHER_SOURCE.search(card):
        problems.append(f"names another source ({m.group(0)!r})")
    return problems


def check_4_revised(t: dict) -> tuple[bool, str]:
    ok, why = check_4(t)
    if t["crashed"] or not (t["fit_card"] or "").strip():
        return ok, why
    role = platform_role_problems(t["fit_card"])
    if ok and not role:
        return True, why + ", bought on the platform"
    return False, "; ".join(([] if ok else [why]) + role)


def _size_ok(wanted: str, listing_size: str) -> bool:
    """The size rule from the Tool Inventory, written again here so the check
    doesn't reuse the code it is checking."""
    pieces = [p for p in re.split(r"[/\s()]+", (listing_size or "").lower()) if p]
    return wanted.lower() in pieces


def check_5(scenario: dict, tries: list[dict]) -> tuple[bool, str]:
    from agent import _parse_query
    from mcp_client import call_tool

    parsed = _parse_query(scenario["query"])
    if parsed["size"] is None or parsed["max_price"] is None:
        return False, f"query has no size or no price limit: {parsed}"
    results = call_tool("search_listings", parsed)

    bad = []
    for listing in results:
        if listing["price"] > parsed["max_price"]:
            bad.append(f"{listing['id']} ${listing['price']:g} > ${parsed['max_price']:g}")
        if not _size_ok(parsed["size"], listing["size"]):
            bad.append(f"{listing['id']} size {listing['size']!r} ≠ {parsed['size']!r}")

    # Tie this re-search to the logged run: same count, same first item, every try.
    for n, t in enumerate(tries, 1):
        if t["crashed"]:
            bad.append(f"logged try {n} crashed")
            continue
        if t["result_count"] != len(results):
            bad.append(f"logged try {n} had {t['result_count']} results, re-search has {len(results)}")
        if results and t["item_title"] != results[0]["title"]:
            bad.append(f"logged try {n} selected {t['item_title']!r}")

    summary = ", ".join(f"{l['id']} {l['size']!r} ${l['price']:g}" for l in results) or "no results"
    if bad:
        return False, f"size={parsed['size']!r} max=${parsed['max_price']:g}: " + "; ".join(bad)
    return True, f"size={parsed['size']!r} max=${parsed['max_price']:g} → {summary}"


# ── report ────────────────────────────────────────────────────────────────────

def main(path: str) -> None:
    runs = parse_log(Path(path).read_text(encoding="utf-8"))
    rows, notes = {}, {}

    for scenario in scenario_module.SCENARIOS:
        number = scenario["criterion"]
        tries = runs.get(scenario["name"])
        if tries is None:
            sys.exit(f"scenario {scenario['name']!r} is not in {path}")
        if number in (1, 2, 3, 4):
            check = {1: check_1, 2: check_2, 3: check_3, 4: check_4}[number]
            results = [check(t) for t in tries]
            rows[number] = [ok for ok, _ in results]
            notes[number] = [f"Try {i}: {'PASS' if ok else 'FAIL'} — {why}"
                             for i, (ok, why) in enumerate(results, 1)]
        elif number == 5:
            ok, why = check_5(scenario, tries)
            rows.setdefault(5, []).append(ok)
            notes.setdefault(5, []).append(
                f"Try {len(rows[5])} (`{scenario['query']}`): {'PASS' if ok else 'FAIL'} — {why}")

    print("| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |")
    print("|---|---|---|---|---|---|---|---|")
    for number in range(1, 6):
        cells = rows[number]
        passes = sum(cells)
        verdict = "MET" if passes >= TARGETS[number] else "MISSED"
        marks = " | ".join("PASS" if ok else "FAIL" for ok in cells)
        print(f"| {TITLES[number]} | {TARGETS[number]} of 5 | {marks} | {verdict} ({passes}/5) |")

    for number in range(1, 6):
        print(f"\n**Criterion {number}**\n")
        for line in notes[number]:
            print(f"- {line}")

    # ── revised criterion 4, added in unit 4 Milestone 4 ──────────────────────
    card_scenario = next(s for s in scenario_module.SCENARIOS if s["criterion"] == 4)
    revised = [check_4_revised(t) for t in runs[card_scenario["name"]]]
    passes = sum(ok for ok, _ in revised)
    verdict = "MET" if passes >= TARGETS[4] else "MISSED"
    print("\n**Criterion 4, revised** (adds: the card presents the item as bought "
          "on the listing's platform)\n")
    print("| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |")
    print("|---|---|---|---|---|---|---|---|")
    marks = " | ".join("PASS" if ok else "FAIL" for ok, _ in revised)
    print(f"| 4r. Fit card facts incl. bought on the platform | 4 of 5 | {marks} | {verdict} ({passes}/5) |\n")
    for i, (ok, why) in enumerate(revised, 1):
        print(f"- Try {i}: {'PASS' if ok else 'FAIL'} — {why}")

    # The same platform check on every fit card in the run, to see whether the
    # criterion-4 item was typical.
    print("\n**Platform check on every fit card in this run**\n")
    print("| Scenario | Item | Cards that misstate the platform |")
    print("|---|---|---|")
    bad_total = card_total = 0
    for scenario in scenario_module.SCENARIOS:
        cards = [t for t in runs[scenario["name"]] if (t["fit_card"] or "").strip()]
        if not cards:
            continue
        bad = [i for i, t in enumerate(runs[scenario["name"]], 1)
               if (t["fit_card"] or "").strip() and platform_role_problems(t["fit_card"])]
        bad_total += len(bad)
        card_total += len(cards)
        tries = ", ".join(f"try {i}" for i in bad) or "none"
        print(f"| {scenario['name']} | {cards[0]['item_title']} ({cards[0]['item_platform']}) "
              f"| {len(bad)} of {len(cards)} ({tries}) |")
    print(f"\nTotal: {bad_total} of {card_total} fit cards misstate the platform.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python score_run.py results/run_<stamp>_<label>.md")
    main(sys.argv[1])
