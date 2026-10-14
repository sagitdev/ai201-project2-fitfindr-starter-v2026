# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->
My search is a plain whole-word keyword match with no plurals or synonyms, so some phrasings of a matching query will score zero and stop the run early. The run also makes two model calls (suggest_outfit and create_fit_card), and either one can return something unusable. One miss in five is room for that; more than one means a real problem in search or a prompt.
---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->
This path never reaches the model. Search is my own code
reading a fixed file, and the decision to stop is an `if` on an empty list in
`agent.py::run_agent`, so the same query gives the same result every time.
There is nothing random on this path, so a single miss means the branch is
broken.
---

## 3. The item search found is the item suggest_outfit received

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

Given a query that matches at least one listing, the `id` of the listing that reaches `suggest_outfit` as `new_item` equals both the `id` stored in `session["selected_item"]` and the `id` of the first result returned by `search_listings`, as shown in the `--trace` output — 5 of 5 tries.

**Why this target:**
Moving the item from search into the session and on to suggest_outfit is my code, not the model, so it should never vary. A failure here would not show in the final output: suggest_outfit would still write a fluent outfit for the wrong item, or for no item. Comparing `id` values in the trace is the only way to catch it, and one mismatch means the session is broken.

---

## 4. The fit card gets the facts right

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

Given a listing and an outfit, the fit card is 2 to 4 sentences (counted by `.`, `!`, or `?` at the end of a sentence), includes the listing's price as a dollar amount (`$24` or `$24.00` for a price of 24.0) and the listing's `platform` name, and does not contain the text `None` — in at least 4 of 5 tries. The wording may change from try to try; the price and platform may not.

**Why this target:**
The caption comes from the model, so the words change on
every run, and it will sometimes run to a fifth sentence or write the price as
"24 bucks." That is why 4 of 5 and not 5 of 5. The price and platform are facts
I pass in from the listing, so missing them more than once means my prompt is
not passing them clearly. The `None` check is there because `brand` is null for
most listings, and a prompt that inserts the brand directly would print "None"
into the caption.

---

## 5. Search respects the size and price limits

Given 5 different queries that each include a size and a price limit, every
listing that `search_listings` returns has a `price` at or below `max_price`
and a `size` that matches by the size rule in my Tool Inventory (lowercase,
split on `/`, spaces, and parentheses, one piece exactly equal to the
requested size) — 5 of 5 queries.

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

**Why this target:**
Filtering by price and size is my own code with no model involved, so it has no reason to vary. The data makes this easy to get wrong: sizes are free text like "S/M", "XL (oversized)", "W30 L30", and "US 9", and a plain substring test lets "S" match "US 9" and "L" match "XL". I use 5 different queries instead of one query 5 times, because the same query on the same file would return the same list every time and prove nothing new.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
