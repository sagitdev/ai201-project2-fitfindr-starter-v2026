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
