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

FitFindr is a command-line agent for thrift shopping. A user types a
request in plain language, like `'vintage graphic tee under $30, size M'`,
and the agent pulls out the description, size, and price limit, then
searches 40 mock listings from depop, poshmark, and thredUp. It picks the
best match, suggests one or two outfits built from pieces in the user's
wardrobe, and writes a short caption they could actually post. If nothing
matches, it stops before the outfit step and says which part of the request
to change: the words, the size, or the price.

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
  - **Size match rule:** lowercase both sizes, then split the listing's
    size on `/`, spaces, and parentheses. A listing matches when one of
    those pieces is exactly equal to the requested size. So `"M"` matches
    `"S/M"` and `"M"`; `"S"` does not match `"US 9"`; `"L"` does not match
    `"XL"`; `"8"` does not match `"W28"`.
    Known limit: a requested `"one size"` does not match listings sized
    `"One Size"`, because the listing's size splits into `"one"` and
    `"size"`. (The data has no sizes written as `"Medium"`.)
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

**How the query is parsed:** Regular expressions, in
`agent.py::_parse_query`. In order: a price range (`$30-$40`,
`30-40 dollars`) uses the upper bound as `max_price`; otherwise a single
price (`$30`, `under 30`, `30 dollars`); then a size, only when it follows
the word "size" (`size M`, `size 8.5`, `size US 8`, `size medium`). What
is left, minus filler words like "looking", "for", "a", and "under",
becomes the description. Each match is cut out of the text so it does not
end up in the description.
I chose regex over asking the model so parsing gives the same result every
time, which criteria 2 and 5 depend on, and so each run costs two model
calls instead of three.
Known limits: written-out prices ("thirty dollars") are not found; a size
without the word "size" ("medium tee") is not found; a range has no
minimum price.

**What moves through the session:** Each step writes its result into the
session and the next step reads it back out, in this order:
`query` → `parsed` (description, size, max_price) → `search_results`
(list of listing dicts) → `selected_item` (`search_results[0]`) →
`outfit_suggestion` (str from suggest_outfit, which also reads
`wardrobe`) → `fit_card` (str from create_fit_card).
On an empty search, `error` is set and `selected_item`,
`outfit_suggestion`, and `fit_card` stay `None`.

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

  No listings matched 'designer ballgown' in size XXS at or under $5. To find something, describe the item with different or fewer words, since nothing in the listings matches 'designer ballgown' at any size or price. A general word like 'tee', 'jeans', 'jacket', or 'dress' is a good start. Your other limits are too tight as well: no listing of any kind is in size XXS at or under $5, so loosen those too.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
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

## MCP: `search_listings` moved behind MCP

- **Tool moved:** `search_listings`. It doesn't call the model, so its
  results are the same on every run and easy to compare. `suggest_outfit`
  and `create_fit_card` are still direct calls.
- **Server (`mcp_server.py`):** registers `search_listings` with FastMCP.
  The typed inputs match the Tool Inventory above (`description: str`,
  `size: str | None`, `max_price: float | None`). The description is
  written for an agent that can't see this code. It gives the units
  (US dollars, inclusive), the size-match rule, the result limit (10),
  the fields in each listing, and the empty case (`[]`, never null or an
  error). The function calls the real implementation, imported under the
  alias `_search_listings_impl`.
- **Client (`agent.py`):** the `search` step of `run_agent()` now calls
  `call_tool("search_listings", {...})` instead of the function.
  `_no_results_message()` still calls `search_listings` directly. Those
  extra searches only explain an empty result, and each MCP call starts a
  new server process. This unit allows only the MCP move and one
  improvement, so they stay as they were.
- **Check:** `python mcp_client.py` lists `search_listings` with
  `description: string`, `size: string (optional)` and
  `max_price: number (optional)`. Comparing the direct call with the MCP
  call on four inputs (`vintage graphic tee` ≤ $30, `jeans` size M,
  `designer ballgown` XXS ≤ $5, `tee`) gave identical lists (`==` is True),
  including both empty cases.
- **End to end:** `python app.py ask 'vintage graphic tee under $30'` and
  `python app.py ask 'designer ballgown size XXS under $5'` printed the
  same output as before the move. Same item ("Y2K Baby Tee — Butterfly
  Print — $18.0 on depop") and same empty-search message. Both model
  prompts were served from cache, so the item passed to `suggest_outfit`
  and `create_fit_card` was byte-for-byte the same as with the direct
  call. **The call changed shape; the return value did not.**

---

## Failure Modes

I triggered each failure on purpose, one at a time, before changing any code,
and then again after adding the handler.

| Failure | How I triggered it | Before Milestone 2 | Handler |
|---|---|---|---|
| Empty search | `python app.py ask 'designer ballgown size XXS under $5'` | Stops after search and says what to change | None needed: `_no_results_message` (unit 3) |
| Empty wardrobe | `python app.py ask 'denim jacket under $50' --empty-wardrobe` | Gives general styling advice, no crash and no empty string | None needed: the empty-wardrobe prompt in `suggest_outfit` (unit 3) |
| Model unavailable | Wrong key via `GEMINI_API_KEY=not-a-real-key-x AI201_CACHE=0`, so `.env` stayed unchanged and nothing was served from cache. Query: `python app.py ask '90s track jacket in size M'` | **Not handled by the agent.** `ModelUnavailable` went straight out of `run_agent()`. Only `app.py`'s catch-all caught it, so it printed `ModelUnavailable: The model rejected your API key…`, exited with code 1, and never said that the search had worked. `run_eval.py` would have logged it as a crash. | **Added:** `run_agent()` catches `ModelUnavailable` at `suggest_outfit` and at `create_fit_card`, puts a message in `session["error"]`, and stops |

**What the agent says now** (real output):

1. Empty search:
   > No listings matched 'designer ballgown' in size XXS at or under $5. To find something, describe the item with different or fewer words, since nothing in the listings matches 'designer ballgown' at any size or price. A general word like 'tee', 'jeans', 'jacket', or 'dress' is a good start. Your other limits are too tight as well: no listing of any kind is in size XXS at or under $5, so loosen those too.

2. Empty wardrobe (outfit section):
   > You haven't added any items to your digital wardrobe yet, but here is how you can style this classic Wrangler piece: Look 1 (Double Denim): Pair it with high-waisted, straight-leg dark wash jeans and a tucked-in white t-shirt… Look 2 (Contrast & Flow): Throw it over a floral midi slip dress and chunky black boots…

3. Model unavailable:
   > Found 90s Track Jacket — Navy/White Stripe ($45 on poshmark), but couldn't suggest an outfit for it: the AI model couldn't be reached. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Your search itself worked, so once that's fixed, run the same query again.

   Trace of that run. It stops at step 4, and `create_fit_card` is never
   called:
   ```
   [4] suggest_outfit
         in:  new_item='90s Track Jacket — Navy/White Stripe', wardrobe=10 items
         out: ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh k…
         →    model unreachable, stopping before create_fit_card
   ```
   The same handler at `create_fit_card` keeps the outfit and says the fit
   card is the step that failed. I tested that path by making
   `create_fit_card` raise `ModelUnavailable` in a test script, because a
   bad key always fails at `suggest_outfit` first.

**Cold read.** I gave all three messages to Claude in a fresh conversation
that couldn't see the code. I asked what it would try next as a user, and told
it not to rewrite them. It could act on all three:
- Empty search: it would change the words and then loosen size and price.
  It pointed out the message doesn't say *how far* to loosen them, so it
  would guess prices until something showed up. I'm leaving this as it is
  for now and noting it as a possible improvement.
- Empty wardrobe: it said this isn't really an error, because it got usable
  looks. The hint "add items to your wardrobe" leads nowhere in the CLI,
  because the CLI has no way to add wardrobe items. That sentence comes
  from the model's reply, not from my code.
- Model unavailable: clear. It would check the key and then make a new
  one. Its only doubt was whether it needs to restart after editing `.env`.
  It doesn't, because each `python app.py ask` reads `.env` fresh.

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

Run: `python run_eval.py --label before` with caching off, 5 tries per
scenario, temperature 0.9. Full log:
[`results/run_2026-11-22_2158_before.md`](results/run_2026-11-22_2158_before.md).
50 runs, 91 model calls, 0 crashes.

**How each try was scored.** `python score_run.py results/run_2026-11-22_2158_before.md`
reads the log and applies each criterion in `criteria.md` exactly as written:

- **1:** no crash and no early stop. The trace shows `search_listings (via MCP)`,
  `suggest_outfit` and `create_fit_card`, and the fit card is not one of
  the tool's fallback messages.
- **2:** the run stopped. The trace has no `suggest_outfit` or
  `create_fit_card` step, and the message names something to change.
- **3:** in the trace, the first search result's id, `selected_item`'s id
  and the `new_item` id passed to `suggest_outfit` are all equal.
- **4:** the fit card has 2-4 sentences (pieces ending in `.`, `!` or `?`),
  the price as `$48` or `$48.00`, and the platform name. It doesn't
  contain `None`.
- **5:** "5 different queries", so Try N is query N, not five repeats of
  one query. The log shows how many listings came back but not every
  listing's size and price, so the script searches again through MCP.
  It checks each listing against `max_price` and against the size rule,
  which it implements separately from `tools.py`. It also checks that all
  five logged tries had the same result count and first item.

The trace now prints listing ids (`first id …`, `id …`, `new_item=lst_… `)
so criterion 3 can be read from the trace, as it says. That is only a
logging change. The agent's behaviour is unchanged.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Search item = selected_item = suggest_outfit's new_item (by id) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2-4 sentences, price, platform, no 'None' | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Search respects size and price limits (5 queries) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Scenarios (`scenarios.py`): 1 `vintage graphic tee under $30` ·
2 `designer ballgown size XXS under $5` ·
3 `silk slip dress in midi length under $40` ·
4 `platform sneakers size 8` (lst_019, $48, poshmark, brand `None`) ·
5 `graphic tee size L under $25`, `vintage top size S under $30`,
`jacket size M under $50`, `chelsea boots size 8.5 under $50`,
`jeans size W30 under $40`. Each criterion-5 query targets one way the
filter could go wrong: L vs XL, S vs "US 9", M vs "M/L", a half size, and a
waist size.

**Real output from one try** (Try 1 of each), produced by
`agent.py::run_agent` through `run_eval.py::run_once`. Trace lines come from
`trace.py::step`, and the fit card comes from `tools.py::create_fit_card`.

Criterion 1 (`vintage graphic tee under $30`):
```
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: 10 results, continuing (first id lst_002)
[3] select_item
      ...
[4] suggest_outfit
      in:  new_item=lst_002 'Y2K Baby Tee — Butterfly Print', wardrobe=10 items
      out: **Outfit 1: Y2K Streetwear** *   Y2K Baby Tee — Butterfly Print *   Baggy straight-leg jeans, dark wash *   Vi…
[5] create_fit_card
      in:  outfit=625 chars, new_item='Y2K Baby Tee — Butterfly Print'
      out: Scored this Y2K Baby Tee with the butterfly print for just $18 and I am obsessed. I threw it on with baggy dar…

Fit card: Scored this Y2K Baby Tee with the butterfly print for just $18 and I am obsessed. I threw it on with baggy dark wash jeans, a vintage denim jacket, and chunky sneakers for that ultimate early 2000s streetwear vibe. Listing it on depop later today so grab it before I change my mind!
```

Criterion 2 (`designer ballgown size XXS under $5`). The message comes from
`agent.py::_no_results_message`:
```
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='xxs', max_price=5.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

stopped early: No listings matched 'designer ballgown' in size XXS at or under $5. To find something, describe the item with different or fewer words, since nothing in the listings matches 'designer ballgown' at any size or price. A general word like 'tee', 'jeans', 'jacket', or 'dress' is a good start. Your other limits are too tight as well: no listing of any kind is in size XXS at or under $5, so loosen those too.
```

Criterion 3 (`silk slip dress in midi length under $40`):
```
[2] search_listings (via MCP)
      in:  description='silk slip dress midi length', size=None, max_price=40.0
      out: 5 items: 90s Silk Slip Dress — Floral, Midi Length, Y2K Baby Tee — Butterfly Print, High-Waisted Denim Shorts — Cutoff … +2 more
      →    branch: 5 results, continuing (first id lst_013)
[3] select_item
      in:  5 results
      out: 90s Silk Slip Dress — Floral, Midi Length ($30.0, depop)
      →    took the first result, the best match (id lst_013)
[4] suggest_outfit
      in:  new_item=lst_013 '90s Silk Slip Dress — Floral, Midi Length', wardrobe=10 items
```

Criterion 4 (`platform sneakers size 8`, lst_019, $48, poshmark):
```
These Platform Sneakers — White Chunky Sole have the ultimate early 2000s energy with their chunky soles and velcro straps. I grabbed them on poshmark for $48 and immediately styled them with a white ribbed tank, baggy dark wash jeans, and a cropped vintage denim jacket. The little bit of sole yellowing just makes them look authentically vintage.
```

Criterion 5, query 1 (`graphic tee size L under $25`), with the
`score_run.py` check underneath:
```
[2] search_listings (via MCP)
      in:  description='graphic tee', size='l', max_price=25.0
      out: 2 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey
      →    branch: 2 results, continuing (first id lst_006)

PASS — size='l' max=$25 → lst_006 'L' $24, lst_033 'L' $19
```
Without limits, `graphic tee` matches 6 listings. The limits left out the
$26 Vintage Graphic Hoodie (size L, over the price limit) and three
listings in other sizes (two `S/M` tops and `W29` cargo pants).

Per-try reasons for all 25 cells are printed by `score_run.py`.

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

One `trace.step()` call per step in `agent.py::run_agent`. The MCP call
shows as `search_listings (via MCP)`. The `→` line records the branch.

**Happy path** (`python app.py ask 'vintage graphic tee under $30' --trace`)

```
[1] parse_query
      in:  'vintage graphic tee under $30'
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: 10 results, continuing
[3] select_item
      in:  10 results
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    took the first result, the best match
[4] suggest_outfit
      in:  new_item='Y2K Baby Tee — Butterfly Print', wardrobe=10 items
      out: **Outfit 1: Y2K Streetwear** *   Y2K Baby Tee — Butterfly Print *   Baggy straight-leg jeans, dark wash *   Vi…
[5] create_fit_card
      in:  outfit=594 chars, new_item='Y2K Baby Tee — Butterfly Print'
      out: Scored this Y2K Baby Tee — Butterfly Print for just $18 and I am obsessed with the early 2000s butterfly graph…
```

**Empty search** (`python app.py ask 'designer ballgown size XXS under $5' --trace`)
stops after step 2, so it never reaches the model:

```
[1] parse_query
      in:  'designer ballgown size XXS under $5'
      out: description='designer ballgown', size='xxs', max_price=5.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='xxs', max_price=5.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
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
