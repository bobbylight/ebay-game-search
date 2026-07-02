# CLAUDE.md

Context for working on this codebase. For setup/usage instructions, see `README.md`.

## Architecture

This is a plain scheduled Python script (run via cron/Task Scheduler), not something
invoked interactively or repeatedly by an agent.

Pipeline, run start-to-finish by `search.py`:

1. **`wishlist.py`** — scrapes the public PriceCharting wishlist page with a hand-rolled
   `HTMLParser` table parser (no BeautifulSoup dependency, intentionally). Returns
   `[{name, platform, list_price}]`. Fragile to PriceCharting markup changes since it's
   parsing an HTML table by structure, not by stable selectors/IDs.
2. **`ebay_client.py`** — OAuth client-credentials flow against eBay, then one Browse
   API search per game (`q = "{name} {platform}"`, `category_ids=139973` to cut down on
   guides/cases/repro noise). No retry/backoff logic.
3. **`store.py`** — SQLite (`output/listings.db`). `listings.item_id` is the primary
   key; `ON CONFLICT` only updates `price`, `bid_count`, `last_seen`, `last_run_id` —
   NOT `game_name`. If the same eBay item ever matches more than one game's search
   query, it keeps whichever `game_name` it was first inserted under.
4. **`report.py`** — generates a single self-contained HTML file: all CSS/JS are inline
   Python string constants in this file, no build step, no external assets. Edit the
   `_CSS`/`_JS` strings directly rather than introducing a bundler/framework.
5. **`notify.py`** — pushes a summary to ntfy.sh if `NTFY_TOPIC` is set.

## Known gotchas

- **`search.py` main loop wraps each `client.search_game()` call in try/except** so one
  bad game (timeout, rate limit, weird title) doesn't abort the whole run. Games that
  fail are skipped for that run, not retried.
- **`get_latest_listings()` only returns rows from `MAX(run_id)`.** If a game's search
  fails (see above) or returns nothing transiently, that game's listings disappear from
  the report entirely until the *next* successful run for that game — there's no
  fallback to "last known good" per game.
- eBay free-tier rate limit is ~5,000 calls/day, application-wide (not per-user). The
  `--results-per-game` default (15) and any scheduling changes should keep
  `games * runs_per_day` comfortably under that.

## Conventions

- No test suite currently exists.
- Dependencies are intentionally minimal: `requests`, `python-dotenv`, `boto3`. Don't
  add a dependency (e.g. BeautifulSoup, a templating engine) unless the hand-rolled
  approach it'd replace is genuinely broken — the minimalism is deliberate, not an
  oversight.
- Python 3.10+ stdlib features (e.g. `X | None` unions) are used freely.
