"""Per-game listing title denylist.

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
"""

GLOBAL_DENYLIST: list[str] = [
    # "lot", "repro", "reproduction",
    "Super Nintendo", # Only looking for NES games for now
    "Super NES",
    " SNES",          # Leading space, while not perfect, to do a "word" match
    "(SNES",
    "famicom",
    "not tested",
]

DENYLIST: dict[str, list[str]] = {
    # "Kid Icarus": ["reproduction", "repro", "manual only"],
    "Godzilla 2": [
        "Monster of Monsters",  # Subtitle of Godzilla 1, which is most often returned from searches
    ]
}

_GLOBAL_DENYLIST_LOWER = [w.lower() for w in GLOBAL_DENYLIST]
_DENYLIST_LOWER = {k.lower(): [w.lower() for w in v] for k, v in DENYLIST.items()}


def is_denied(game_name: str, title: str) -> bool:
    """True if `title` should be excluded from results for `game_name`."""
    title_lower = title.lower()
    if any(w in title_lower for w in _GLOBAL_DENYLIST_LOWER):
        return True
    words = _DENYLIST_LOWER.get(game_name.lower())
    if not words:
        return False
    return any(w in title_lower for w in words)
