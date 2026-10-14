# Data Notes (Milestone 1)

## Where the data comes from
- data/listings.json: 40 fixed mock listings (modeled on depop,
  poshmark, thredUp). The agent searches only this file, not the web.
  In a real product, search_listings would call a platform API instead;
  the agent loop would not change.
- Example wardrobe (10 items) in data/wardrobe_schema.json is sample
  data for development. suggest_outfit takes the wardrobe as a
  parameter, so any wardrobe in the same format works.

## Listing fields
id, title, description, category, style_tags (list), size, condition,
price (float), colors (list), brand (may be null), platform

search_listings filters on:
- description -> title, description, style_tags
- size        -> size
- max_price   -> price

## Things to handle
- size is free text: "M", "S/M", "L", "XL (oversized)", "W30 L30", "W28".
  Exact string match misses "S/M" when the user asks for "M".
- brand and notes can be null.
- max_price may be missing; skip the price filter t- max_price may be missing;items": [ ... ]}
Empty wardrobEmpty wardrobEmpty wardrck waEmpty wardrobEmpty wardrobEmpty wardrck waEmpty wardrobEmptyry, colors, style_tags, notes (optional)
Categories: tops, bottoms, outerwear, shoes, accessories

## Style vocabulary mismatch
style_tags are free text in both files. Some overlap (streetwear,
vintage, denim, classic, grunge, earth tones), but a usevintage, denim, classic, grunge, earth tones), but a usevintag. "retro" vs "vintage").
- suggest_outfit: lower risk if - suggest_outf the matching, since it
  understands similar meanings and also uses colors and category.
- search_listings: higher risk if it uses exact keyword matching.
  A synonym can return an empty search even when a good match exists.
  Options: search title + description too, a small   Options: search title + description too, a small   Options: search tit P  Options: search title + description too, a small   Optionsee")
  still finds the matching v  still finds the matching v  still finds the matching v  still finds the matching v  still fer $5'

## Query parsing (decide in the loop milestone)
search_listings receives already-parsed values; parsing happens in
agent.py before the tool is called.
- "under thirty dollars": regex finds no number; the model can parse it.
- "30-40 dollars": search_listings has max_price only, no min_price.
  Plan: use the upper bound (40.0) as max_price; note it as a known limit.
EOF

## Milestone 3 notes

### Must remember when building the loop
- Criterion 2: when search is empty, the stop message must say what to
  change (e.g. raise the price limit, try another size or fewer words),
  not just "no results".
- Criterion 3: the trace must show three ids: the first search result,
  session["selected_item"], and the new_item that reached suggest_outfit.
  Add trace.step() calls for all three.
- Criterion 4: the create_fit_card prompt must not insert brand directly,
  since brand is null for most listings.

### Criterion 5 test plan (pick queries in unit 4)
Use 5 different queries, each with a size and a price limit. Include at
least one where a substring test would go wrong:
- a size "S" query (must not match "US 9")
- a size "L" query (must not match "XL")
- a size "M" query (must match "S/M")

### Criterion candidates not used
- Synonym query: 'retro graphic tee' finds a vintage graphic tee.
  (Known limit; possible unit 4 improvement.)
- Empty wardrobe: the agent still completes all three tool calls.
- No invented pieces: every wardrobe piece named in the outfit exists
  in the wardrobe.
