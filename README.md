# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches `data/listings.json` and returns the listings
  that match the description, and optionally a size and a price ceiling,
  best match first.
- **Inputs:**
  - `description` (str): keywords for what the user wants, e.g.
    `"vintage graphic tee"`.
  - `size` (str | None): the size to filter by, e.g. `"M"`. `None` skips
    the size filter.
  - `max_price` (float | None): the highest price allowed, inclusive
    (a $30.0 item passes `max_price=30.0`). `None` skips the price filter.
- **Returns:** `list[dict]` — full listing dicts, each with `id`, `title`,
  `description`, `category`, `style_tags` (list), `size`, `condition`,
  `price` (float), `colors` (list), `brand` (str or None), `platform`.
  Sorted by score, highest first, at most `config.SEARCH_RESULT_LIMIT`
  items.
  - **Score:** split `description` into lowercase words. Count how many
    of those words appear as whole words in the listing's `title`,
    `description`, or `style_tags` (so `"tee"` does not count inside
    `"steel"`). Listings scoring 0 are dropped.
    Known limit: no plurals or synonyms, so `"tees"` does not match
    `"tee"` and `"retro"` does not match `"vintage"`.
  - **Size match rule:** lowercase both sizes and split them on `/`,
    spaces, and parentheses. A listing matches when one of its pieces is
    exactly equal to the requested size. So `"M"` matches `"S/M"` and
    `"M"`; `"S"` does not match `"US 9"`; `"L"` does not match `"XL"`;
    `"8"` does not match `"W28"`.
    Known limit: `"M"` does not match a size written as `"Medium"`.
- **When it has nothing:** returns `[]` (an empty list). Never `None`,
  never raises.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits that combine the
  new item with pieces from the user's wardrobe.
- **Inputs:**
  - `new_item` (dict): one listing dict, as returned by `search_listings`.
  - `wardrobe` (dict): `{"items": [...]}`, each item with `id`, `name`,
    `category`, `colors`, `style_tags`, `notes` (may be None), as in
    `data/wardrobe_schema.json`.
- **Returns:** `str` — a non-empty string with one or two outfit
  suggestions, each naming the wardrobe pieces it uses by their `name`.
- **When it has nothing:** if `wardrobe["items"]` is `[]`, it still returns
  a non-empty string: general styling advice for the new item alone.
  Never returns `""`, never raises.

### `create_fit_card`

- **What it does:** Asks the model to write a short caption someone would
  actually post about the find.
- **Inputs:**
  - `outfit` (str): the outfit text returned by `suggest_outfit`.
  - `new_item` (dict): the same listing dict passed to `suggest_outfit`.
- **Returns:** `str` — a caption of 2 to 4 sentences that reads like a
  real post, mentions the item's `title`, `price`, and `platform` once
  each, and does not assume `brand` is present.
- **When it has nothing:** if `outfit` is empty or only whitespace, it does
  not call the model and returns a message saying no outfit was given to
  write a caption for. Never raises.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message
in `session["error"]` that says which filter to change (raise the price
limit, remove the size, or use different words), and stop without calling
`suggest_outfit`. Otherwise, store the first result (the highest-scoring
listing) in `session["selected_item"]` and pass it to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regular expressions, in `agent.py::_parse_query`. In order: a price range (`$30-$40`,`30-40 dollars`) uses the upper bound as `max_price`; otherwise a single price (`$30`, `under 30`, `30 dollars`); then a size, only when it follows the word "size" (`size M`, `size 8.5`, `size US 8`, `size medium`). What is left, minus filler words like "looking", "for", "a", and "under", becomes the description. Each match is cut out of the text so it does not end up in the description. I chose regex over asking the model so parsing gives the same result every time, which criteria 2 and 5 depend on, and so each run costs two model calls instead of three. Known limits: written-out prices ("thirty dollars") are not found; a size without the word "size" ("medium tee") is not found; a range has no
minimum price.
<!-- regex, string splitting, or asking the model — say which -->

**What moves through the session:** Each step writes its result into the session and the next step reads it back out, in this order: `query` → `parsed` (description, size, max_price) → `search_results`
(list of listing dicts) → `selected_item` (`search_results[0]`) → `outfit_suggestion` (str from suggest_outfit, which also reads `wardrobe`) → `fit_card` (str from create_fit_card). On an empty search, `error` is set and `selected_item`, `outfit_suggestion`, and `fit_card` stay `None`.
<!-- which fields, in what order -->

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Y2K Streetwear**
*   Y2K Baby Tee — Butterfly Print
*   Baggy straight-leg jeans, dark wash
*   Vintage black denim jacket
*   Chunky white sneakers
*   Black crossbody bag

*Why it works:* The fitted tee balances the volume of the baggy jeans while leaning into effortless retro streetwear.

**Outfit 2: Casual Contrast**
*   Y2K Baby Tee — Butterfly Print
*   Wide-leg khaki trousers
*   Black combat boots
*   Brown leather belt
*   Black crossbody bag

*Why it works:* Pairing the sweet, feminine top with utilitarian trousers and combat boots creates a cool, balanced contrast.

  Fit card: Found this Y2K Baby Tee — Butterfly Print while digging through the racks and knew I had to grab it for $18. I love pairing it with baggy dark wash jeans and a black denim jacket for that effortless retro streetwear vibe. Listed it on depop this morning if anyone wants to steal this look.

0 model calls this session, 2 served from cache
```

**The empty-search path**

```
$ python app.py ask 'designer ballgown size XXS under $5'

  No listings matched 'designer ballgown' in size XXS at or under $5. To find something, describe the item with different or fewer words, since nothing in the listings matches 'designer ballgown' at any size or price. A general word like 'tee', 'jeans', 'jacket', or 'dress' is a good start.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits likea small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki','description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags':['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit 1: Casual Streetwear**
- Thrifted item: Vintage Levi's 501 Jeans — Medium Wash
- Tops: White ribbed tank top
- Outerwear: Vintage black denim jacket
- Shoes: Chunky white sneakers
- Accessories: Black crossbody bag

*Why it works:* A classic denim-on-denim pairing that feels effortless, balanced by crisp white sneakers and a sleek crossbody.

***

**Outfit 2: Cozy & Relaxed**
- Thrifted item: Vintage Levi's 501 Jeans — Medium Wash
- Tops: Oversized grey crewneck sweatshirt
- Shoes: Black combat boots
- Accessories: Brown leather belt

*Why it works:* The fitted 501s anchor the volume of the oversized sweatshirt, while boots and a belt add a touch of everyday structure.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these Vintage Levi's 501 Jeans — Medium Wash at the bins and they fit like an absolute dream. I threw them on with my beat-up white sneakers for that easy, everyday running-around look. Snagged them on depop for just $38.
```

**Empty cases**

```
$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
It looks like you haven't added any wardrobe items yet, but these vintage Levi's 501s are a blank canvas for endless looks.
Here are two easy ways to style them:
* **The Casual Classic:** Pair them with a crisp white t-shirt, a leather belt, and retro sneakers for an effortless everyday outfit.
* **Elevated Streetwear:** Layer an oversized blazer over a simple black tank or hoodie, and finish the look with chunky loafers or boots.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
Can't write a fit card for Vintage Levi's 501 Jeans — Medium Wash: no outfit was given.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I pasted my empty-search message into a fresh AI
  conversation, with no context about the app, and asked what it would try
  next after reading it, without rewriting the message.
- *What came back:* For 'designer ballgown size XXS under $5' it knew to
  try "dress", but said it would keep XXS and $5, because the message only
  said "designer ballgown" was the problem. That would likely be a second
  empty search, since no listing of any kind is XXS at or under $5.
- *What I changed:* When the words are the problem, `_no_results_message`
  now also counts listings of any kind within the size and price limit,
  using the same size rule as search, and says whether those limits need
  loosening too. Re-asked with the new message: the reader now loosens the
  size and price as well as changing the words.

**Moment 2**

- *What I asked for:* I asked AI to help build `create_fit_card`, then ran
  it three times on the same item, as Milestone 4 asks.
- *What came back:* The three captions were word-for-word identical, which
  looked like the model wasn't varying at all.
- *What I changed:* `TEMPERATURE` in `config.py` was already 0.9, so the
  cause was the cache: identical prompts return the saved answer. Running
  with `AI201_CACHE=0` gave different wording each time while the price
  and platform stayed correct, which is what criterion 4 expects.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
