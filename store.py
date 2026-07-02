import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "output" / "listings.db"

_DDL = """
CREATE TABLE IF NOT EXISTS runs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS listings (
    item_id       TEXT PRIMARY KEY,
    game_name     TEXT NOT NULL,
    title         TEXT NOT NULL,
    price         REAL,
    currency      TEXT,
    buying_option TEXT,
    end_time      TEXT,
    bid_count     INTEGER,
    condition     TEXT,
    seller        TEXT,
    url           TEXT,
    image_url     TEXT,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    last_run_id   INTEGER NOT NULL REFERENCES runs(id)
);
"""


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript(_DDL)
    return con


def start_run() -> int:
    con = _conn()
    cur = con.execute(
        "INSERT INTO runs (started_at) VALUES (?)",
        (datetime.now(timezone.utc).isoformat(),),
    )
    run_id = cur.lastrowid
    con.commit()
    con.close()
    return run_id


def upsert_listings(items: list[dict], game_name: str, run_id: int) -> int:
    now = datetime.now(timezone.utc).isoformat()
    con = _conn()
    count = 0
    for item in items:
        options = item.get("buyingOptions", [])
        buying_option = "AUCTION" if "AUCTION" in options else (options[0] if options else None)

        # Auctions expose currentBidPrice; fixed-price listings expose price.
        price_block = item.get("currentBidPrice") or item.get("price")
        price = float(price_block["value"]) if price_block else None
        currency = price_block.get("currency") if price_block else None

        con.execute(
            """
            INSERT INTO listings
                (item_id, game_name, title, price, currency, buying_option,
                 end_time, bid_count, condition, seller, url, image_url,
                 first_seen, last_seen, last_run_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(item_id) DO UPDATE SET
                price         = excluded.price,
                bid_count     = excluded.bid_count,
                last_seen     = excluded.last_seen,
                last_run_id   = excluded.last_run_id
            """,
            (
                item.get("itemId"),
                game_name,
                item.get("title", ""),
                price,
                currency,
                buying_option,
                item.get("itemEndDate"),
                item.get("bidCount"),
                item.get("condition"),
                (item.get("seller") or {}).get("username"),
                item.get("itemWebUrl"),
                (item.get("image") or {}).get("imageUrl"),
                now, now, run_id,
            ),
        )
        count += 1
    con.commit()
    con.close()
    return count


def get_new_listings(run_id: int) -> list[dict]:
    """Returns listings first seen in this run (inserted, not just updated)."""
    con = _conn()
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT l.* FROM listings l
        JOIN runs r ON r.id = ?
        WHERE l.last_run_id = ?
          AND l.first_seen >= r.started_at
        ORDER BY l.game_name, l.buying_option, l.price ASC
        """,
        (run_id, run_id),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_latest_listings() -> list[dict]:
    """Returns all listings from the most recent run, excluding ended auctions."""
    con = _conn()
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT * FROM listings
        WHERE last_run_id = (SELECT MAX(id) FROM runs)
          AND (end_time IS NULL OR end_time > datetime('now'))
        ORDER BY
            game_name,
            CASE buying_option WHEN 'AUCTION' THEN 0 ELSE 1 END,
            COALESCE(end_time, '9999') ASC,
            price ASC
        """
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]
