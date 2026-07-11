#!/usr/bin/env python3
"""eBay NES Game Tracker — entrypoint."""

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import denylist
import notify
import wishlist as wl
from ebay_client import EbayClient
from store import start_run, upsert_listings, get_latest_listings, get_new_listings
from report import generate


def _upload_to_s3(report_path: Path, bucket: str, key: str) -> str:
    import boto3
    s3 = boto3.client("s3")
    s3.upload_file(
        str(report_path),
        bucket,
        key,
        ExtraArgs={
            "ContentType": "text/html; charset=utf-8",
            "CacheControl": "no-cache",
        },
    )
    return f"https://{bucket}.s3.amazonaws.com/{key}"


def _published_url() -> str | None:
    domain = os.getenv("PUBLISHED_REPORT_DOMAIN", "").rstrip("/")
    key = os.getenv("EBAY_S3_KEY", "").lstrip("/")
    if domain and key:
        return f"{domain}/{key}"
    return None


def _send_notification(new_listings: list[dict], report_url: str | None) -> None:
    topic = os.getenv("NTFY_TOPIC", "")
    if not topic or not new_listings:
        return

    by_game: dict[str, dict] = defaultdict(lambda: {"auction": 0, "bin": 0, "min_price": None})
    for lst in new_listings:
        key = "auction" if lst.get("buying_option") == "AUCTION" else "bin"
        by_game[lst["game_name"]][key] += 1
        p = lst.get("price")
        if p is not None:
            p += lst.get("shipping_price") or 0
            cur = by_game[lst["game_name"]]["min_price"]
            by_game[lst["game_name"]]["min_price"] = p if cur is None else min(cur, p)

    total = len(new_listings)
    n_games = len(by_game)
    title = f"eBay NES: {total} new listing{'s' if total != 1 else ''} across {n_games} game{'s' if n_games != 1 else ''}"

    lines = []
    for game, counts in sorted(by_game.items()):
        parts = []
        if counts["auction"]:
            parts.append(f"{counts['auction']} auction{'s' if counts['auction'] != 1 else ''}")
        if counts["bin"]:
            parts.append(f"{counts['bin']} BIN")
        price_str = f" (from ${counts['min_price']:.2f})" if counts["min_price"] is not None else ""
        lines.append(f"🎮 {game}: {', '.join(parts)}{price_str}")

    body = "\n".join(lines)
    ok = notify.send(topic, title, body, url=report_url)
    print(f"Notification {'sent' if ok else 'failed'} ({total} new listings)")


def main():
    parser = argparse.ArgumentParser(description="Track eBay listings for your NES wishlist")
    parser.add_argument("--results-per-game", type=int, default=15, metavar="N",
                        help="Max eBay results to fetch per game; report shows all fetched, cheapest first (default: 15)")
    parser.add_argument("--report-only", action="store_true",
                        help="Skip fetching; regenerate report from existing DB")
    args = parser.parse_args()

    wishlist_url = os.getenv("PRICECHARTING_WISHLIST_URL", "")
    if not wishlist_url:
        print("ERROR: PRICECHARTING_WISHLIST_URL not set in .env", file=sys.stderr)
        sys.exit(1)

    print("Fetching wishlist ...")
    games = wl.fetch(wishlist_url)
    print(f"  {len(games)} games")

    if args.report_only:
        listings = get_latest_listings()
        report_path = generate(listings, games, limit_per_game=args.results_per_game)
        print(f"Report (from cache) → {report_path}")
        return

    app_id = os.getenv("EBAY_APP_ID", "")
    cert_id = os.getenv("EBAY_CERT_ID", "")
    if not app_id or not cert_id:
        print("ERROR: EBAY_APP_ID and EBAY_CERT_ID must be set in .env", file=sys.stderr)
        sys.exit(1)

    buyer_zip = os.getenv("EBAY_BUYER_ZIP", "") or None
    client = EbayClient(app_id, cert_id, buyer_zip=buyer_zip)
    run_id = start_run()

    total = 0
    for game in games:
        try:
            items = client.search_game(
                game["name"],
                platform=game.get("platform", "NES"),
                limit=args.results_per_game,
            )
        except Exception as e:
            print(f"  {game['name']}: FAILED ({e})", file=sys.stderr)
            continue

        # Filter out auctions whose titles have keywords that indicate they're NOT what we're looking
        # for. Typical with e.g. games with sequels, or on multiple platforms, etc., where we might
        # get false positives from our search results
        fetched = len(items)
        items = [it for it in items if not denylist.is_denied(game["name"], it.get("title", ""))]
        denied = fetched - len(items)

        n = upsert_listings(items, game["name"], run_id)
        total += n
        suffix = f" ({denied} denylisted)" if denied else ""
        print(f"  {game['name']}: {len(items)} results{suffix}")

    new_listings = get_new_listings(run_id)

    listings = get_latest_listings()
    report_path = generate(listings, games, limit_per_game=args.results_per_game)
    print(f"Done — {total} listings stored, {len(listings)} active, {len(new_listings)} new")
    print(f"Report → {report_path}")

    report_url = None
    bucket = os.getenv("EBAY_S3_BUCKET", "")
    if bucket:
        key = os.getenv("EBAY_S3_KEY", "ebay-game-search/report.html")
        try:
            _upload_to_s3(report_path, bucket, key)
            report_url = _published_url()
            print(f"Uploaded → {report_url or f'https://{bucket}.s3.amazonaws.com/{key}'}")
        except Exception as e:
            print(f"S3 upload failed: {e}", file=sys.stderr)

    _send_notification(new_listings, report_url)


if __name__ == "__main__":
    main()
