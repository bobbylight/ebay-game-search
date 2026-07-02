import requests
from html.parser import HTMLParser

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_table = False
        self._in_cell = False
        self._rows: list[list[str]] = []
        self._row: list[str] = []
        self._cell = ""

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table = True
        if self._in_table and tag == "tr":
            self._row = []
        if self._in_table and tag in ("td", "th"):
            self._in_cell = True
            self._cell = ""

    def handle_endtag(self, tag):
        if tag == "table":
            self._in_table = False
        if self._in_table and tag in ("td", "th"):
            self._row.append(self._cell.strip())
            self._in_cell = False
        if self._in_table and tag == "tr" and self._row:
            self._rows.append(self._row)
            self._row = []

    def handle_data(self, data):
        if self._in_cell:
            self._cell += data

    @property
    def rows(self):
        return self._rows


def fetch(url: str) -> list[dict]:
    """Fetch a public PriceCharting wishlist. Returns [{name, platform, list_price}]."""
    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()

    parser = _TableParser()
    parser.feed(resp.text)

    games = []
    seen: set[str] = set()
    for row in parser.rows:
        if len(row) < 3 or row[0].lower() == "photo":
            continue
        name_parts = [p.strip() for p in row[1].split("\n") if p.strip()]
        if not name_parts:
            continue
        name = name_parts[0]
        platform = name_parts[1] if len(name_parts) > 1 else ""
        try:
            list_price = float(row[2].replace("$", "").replace(",", ""))
        except ValueError:
            list_price = None

        if name and name not in seen:
            seen.add(name)
            games.append({"name": name, "platform": platform, "list_price": list_price})

    return games
