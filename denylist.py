"""Per-game listing title denylist, plus a seller username denylist.

Hard-coded rather than stored in the DB: games are ephemeral in this pipeline
(removed from the wishlist once bought), so there's little value in a
persisted/editable-at-runtime filter for a game that will stop being searched
for soon anyway. Just edit this file when a game's search results need
tuning.

Keys are game names as they appear on the PriceCharting wishlist (matched
case-insensitively). Values are words/phrases that, if found
case-insensitively in a listing title, cause that listing to be skipped for
that game.

GLOBAL_DENYLIST holds words/phrases applied to every game's search results
(e.g. junk that shows up across the board like "lot" or "repro").

USER_DENYLIST holds eBay seller usernames (matched case-insensitively) whose
listings are always excluded, regardless of title, e.g. known repro sellers.
"""

GLOBAL_DENYLIST: list[str] = [
    # "lot", "repro", "reproduction",
    "Super Nintendo", # Only looking for NES games for now
    "Super NES",
    " SNES",          # Leading space, while not perfect, to do a "word" match
    "(SNES",
    "gameboy",        # not looking for Game Boy games for now
    "game boy",
    "famicom",
    "not tested",     # Skip games that may not actually work
    "untested",
]

PER_GAME_DENYLIST: dict[str, list[str]] = {
    # "Kid Icarus": ["reproduction", "repro", "manual only"],
    "Batman The Video Game": [
        "Return of the Joker",  # Actually one of the sequels/other Batman games
    ],
    "Bubble Bobble Part 2": [
        "1986"                  # First game's launch year
    ],
    "Chip and Dale Rescue Rangers 2": [
        "Rescue Rangers 1",
        "1990"                  # Rescue Rangers 1 was released in 1990, 2 in 1994
    ],
    "Godzilla 2": [
        "1988",                 # Godzilla 1 JP
        "1989",                 # Godzilla 1 US
        "Monster of Monsters",  # Subtitle of Godzilla 1, which is most often returned from searches
    ],
    "Power Blade": [
        "Power Blade 2",
    ],
    "Tiny Toon Adventures": [
        "Adventures 2",         # Sequel
        "Trouble in Wackyland", # Sequel
    ],
}

USER_DENYLIST: list[str] = [
    "aussie-export-bargains",  # Only sells PAL games obviously
    "malja1990",               # Sells reproductions almost exclusively, labeled as such
    "retro88",                 # Selling a single game, modified Gun-Nac cart with 2500+ games
]

_GLOBAL_DENYLIST_LOWER = [w.lower() for w in GLOBAL_DENYLIST]
_PER_GAME_DENYLIST_LOWER = {k.lower(): [w.lower() for w in v] for k, v in PER_GAME_DENYLIST.items()}
_USER_DENYLIST_LOWER = {u.lower() for u in USER_DENYLIST}


def is_denied(game_name: str, title: str, seller: str | None = None) -> bool:
    """True if `title` should be excluded from results for `game_name`."""
    if seller and seller.lower() in _USER_DENYLIST_LOWER:
        return True
    title_lower = title.lower()
    if any(w in title_lower for w in _GLOBAL_DENYLIST_LOWER):
        return True
    words = _PER_GAME_DENYLIST_LOWER.get(game_name.lower())
    if not words:
        return False
    return any(w in title_lower for w in words)
