from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path(__file__).parent / "output" / "report.html"

# 16x13 matches the .82rem (~13px) size of .pc-price text at native resolution.
_PC_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAANCAYAAACgu+4kAAAABHNCSVQICAgIfAhkiAAAAKhJREFU"
    "KJFjZCACMJZd/Q9j/+/SZkSRI0UzNkMgjMIzbxlZOYWIcQ26ISzYbCAFMBFr2//NFYFkGfC/S5ux"
    "dqnTfz3BU5/+d2kzwnDtUqf/DAwMDIz4vICsEAbmN54xT6w3OQnj4zQAm2aivYCuuTl6H2Nz9D7G"
    "Z/c/bcdQjOwCGLt2qdNXQjajuA6Zo2cr7kxIM4oD0A1ojt5HMHUiA5QwIFUzAwMDAwA9X03AGa9W"
    "/QAAAABJRU5ErkJggg=="
)

_CSS = """
* { box-sizing: border-box; }
body { font-family: system-ui, sans-serif; max-width: 1100px; margin: 2rem auto; padding: 0 1rem; background: #f0f2f5; color: #1a1a1a; }
h1 { margin-bottom: .25rem; display: flex; align-items: center; gap: .5rem; }
.meta { color: #666; font-size: .9rem; margin-bottom: 1rem; }
.top-controls { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; margin-bottom: 1.75rem; }
.summary { display: flex; gap: 1rem; flex-wrap: wrap; }
.stat { background: #fff; border-radius: 8px; padding: .75rem 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,.1); min-width: 120px; }
.stat .n { font-size: 1.8rem; font-weight: 700; color: #2563eb; line-height: 1; }
.stat .label { font-size: .78rem; color: #666; margin-top: .2rem; }
.filter-box { display: flex; align-items: center; gap: .5rem; }
.filter-box label { font-size: .85rem; color: #555; white-space: nowrap; }
.filter-box input { padding: .4rem .7rem; border: 1px solid #ccc; border-radius: 6px; font-size: .9rem; width: 220px; outline: none; }
.filter-box input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.15); }
.legend { display: flex; align-items: center; gap: .6rem; font-size: .82rem; color: #666;
          padding: .4rem .7rem; background: #fff; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,.08); flex-wrap: wrap; }
.legend strong { white-space: nowrap; }
.legend-filter { background: none; border: 1px solid #ddd; border-radius: 6px; padding: .3rem .65rem;
                 cursor: pointer; font-size: .82rem; color: #555; font-family: inherit;
                 display: inline-flex; align-items: center; gap: .35rem;
                 transition: opacity .15s, background .1s; }
.legend-filter:hover { background: #f0f2f5; border-color: #bbb; }
.legend-filter.off { opacity: .3; border-style: dashed; }
details.game { background: #fff; border-radius: 8px; margin-bottom: .6rem; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
details.game summary { display: flex; align-items: center; gap: .75rem; padding: .8rem 1.25rem;
                        cursor: pointer; list-style: none; border-radius: 8px; flex-wrap: wrap; }
details.game summary::-webkit-details-marker { display: none; }
details.game summary::marker { display: none; }
details.game summary::before { content: '▸'; font-size: 1.2rem; color: #bbb; flex-shrink: 0;
                                transition: transform .15s; line-height: 1; }
details.game[open] summary::before { transform: rotate(90deg); }
details.game summary:hover { background: #f8f9ff; }
details.game[open] summary { border-bottom: 1px solid #f0f0f0; border-radius: 8px 8px 0 0; }
.game-body { padding: .75rem 1.25rem 1rem; }
details.game summary h2 { margin: 0; font-size: 1.05rem; }
.pc-price   { font-size: .82rem; color: #999; }
.pc-icon    { width: 16px; height: 13px; vertical-align: -1px; }
.ebay-range { font-size: .82rem; color: #2563eb; font-weight: 600; display: inline-flex; align-items: center; gap: .25rem; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: .35rem .6rem; font-size: .75rem; color: #999; border-bottom: 1px solid #eee;
     text-transform: uppercase; letter-spacing: .04em; user-select: none; }
th.sortable { cursor: pointer; }
th.sortable:hover { color: #444; }
th.sort-asc::after  { content: ' ↑'; color: #2563eb; }
th.sort-desc::after { content: ' ↓'; color: #2563eb; }
td { padding: .45rem .6rem; border-bottom: 1px solid #f4f4f4; font-size: .87rem; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f8f9ff; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
.thumb { width: 40px; height: 40px; object-fit: contain; }
.badge { display: inline-block; padding: .1rem .4rem; border-radius: 4px; font-size: .73rem; font-weight: 600; white-space: nowrap; }
.auction { background: #fef3c7; color: #92400e; }
.bin     { background: #dbeafe; color: #1e40af; }
.deal    { background: #dcfce7; color: #166534; }
.count-badges { margin-left: auto; display: flex; gap: .35rem; flex-shrink: 0; align-items: center; }
details.game.hidden-by-filter, details.game.hidden-by-type { display: none; }
tr.hidden-by-type, tr.hidden-by-deal, tr.hidden-by-new { display: none; }
.ship-note { font-size: .78rem; color: #999; white-space: nowrap; }
.ship-note.free { color: #16a34a; }
.ship-note.unknown { font-style: italic; }
.ending-soon { color: #dc2626; font-weight: 600; }
.good-deal { color: #16a34a; font-weight: 700; }
.new-badge { background: #dcfce7; color: #166534; border: 1px solid #86efac;
             display: inline-block; padding: .1rem .45rem; border-radius: 4px;
             font-size: .7rem; font-weight: 700; white-space: nowrap; }
.no-listings { background: #fff; border-radius: 8px; padding: 1rem 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,.1); margin-top: 1rem; }
.no-listings h3 { margin: 0 0 .5rem; font-size: .9rem; color: #888; font-weight: 600; }
.no-listings ul { margin: 0; padding-left: 1.25rem; columns: 3; font-size: .85rem; color: #aaa; gap: 1rem; }

@media (max-width: 640px) {
  body { padding: 0 .5rem; margin: 1rem auto; }
  .top-controls { flex-direction: column; align-items: flex-start; }
  .filter-box input { width: 100%; }
  .no-listings ul { columns: 1; }
  .game-body { padding: .5rem .6rem .75rem; }
  table thead { display: none; }
  table tbody tr { display: grid; grid-template-columns: 132px 1fr; gap: 0 .5rem;
                   border: 1px solid #e5e7eb; border-radius: 6px;
                   margin-bottom: .5rem; padding: .4rem .5rem; background: #fafafa; }
  table tbody tr:last-child { margin-bottom: 0; }
  table tbody td:first-child { grid-column: 1; grid-row: 1 / 8; display: flex;
                                align-items: flex-start; padding: .2rem 0 0; border: none; }
  table tbody td:first-child .thumb { width: 128px; height: 128px; }
  table tbody td:not(:first-child) { grid-column: 2; display: flex; align-items: baseline;
                                      gap: .5rem; padding: .15rem 0; border: none; font-size: .87rem; }
  table tbody td[data-label]::before { content: attr(data-label); min-width: 52px;
    font-size: .7rem; color: #aaa; text-transform: uppercase; letter-spacing: .04em; flex-shrink: 0; }
  table tbody td[data-label=""]::before { display: none; }
}
"""

_JS = """
document.addEventListener('DOMContentLoaded', function () {

    // --- Game name filter ---
    document.getElementById('game-filter').addEventListener('input', function () {
        const q = this.value.toLowerCase();
        document.querySelectorAll('details.game').forEach(function (section) {
            const name = section.querySelector('h2').textContent.toLowerCase();
            section.style.display = name.includes(q) ? '' : 'none';
        });
    });

    // --- Type + deal legend filters ---
    function updateGameVisibility() {
        document.querySelectorAll('details.game').forEach(function (section) {
            const hasVisible = Array.from(section.querySelectorAll('tbody tr')).some(function (tr) {
                return !tr.classList.contains('hidden-by-type') && !tr.classList.contains('hidden-by-deal') && !tr.classList.contains('hidden-by-new');
            });
            section.classList.toggle('hidden-by-filter', !hasVisible);
        });
    }

    document.querySelectorAll('.legend-filter[data-filter="auction"], .legend-filter[data-filter="bin"]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const type = btn.dataset.filter;
            const nowOff = btn.classList.toggle('off');
            document.querySelectorAll('tr[data-type="' + type + '"]').forEach(function (tr) {
                tr.classList.toggle('hidden-by-type', nowOff);
            });
            updateGameVisibility();
        });
    });

    var dealBtn = document.querySelector('.legend-filter[data-filter="deal"]');
    if (dealBtn) {
        dealBtn.addEventListener('click', function () {
            var nowOff = dealBtn.classList.toggle('off');
            document.querySelectorAll('tbody tr').forEach(function (tr) {
                if (nowOff) {
                    tr.classList.remove('hidden-by-deal');
                } else {
                    var pcPrice = parseFloat(tr.dataset.pcPrice || '');
                    var priceTd = tr.querySelector('td[data-price]');
                    var price = parseFloat(priceTd ? priceTd.dataset.price : '');
                    tr.classList.toggle('hidden-by-deal', isNaN(pcPrice) || price >= pcPrice);
                }
            });
            updateGameVisibility();
        });
    }

    var newBtn = document.querySelector('.legend-filter[data-filter="new"]');
    if (newBtn) {
        newBtn.addEventListener('click', function () {
            var nowOff = newBtn.classList.toggle('off');
            document.querySelectorAll('tbody tr').forEach(function (tr) {
                tr.classList.toggle('hidden-by-new', !nowOff && tr.dataset.new !== 'true');
            });
            updateGameVisibility();
        });
    }

    // --- Sortable tables ---
    function sortTable(th, asc) {
        const table = th.closest('table');
        const tbody = table.querySelector('tbody');
        const col   = th.dataset.col;

        table.querySelectorAll('th.sortable').forEach(function (h) {
            h.classList.remove('sort-asc', 'sort-desc');
            h.dataset.asc = '';
        });
        th.classList.add(asc ? 'sort-asc' : 'sort-desc');
        th.dataset.asc = asc ? 'true' : 'false';

        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort(function (a, b) {
            const av = a.querySelector('td[data-' + col + ']')?.dataset[col] ?? '';
            const bv = b.querySelector('td[data-' + col + ']')?.dataset[col] ?? '';
            if (col === 'price' || col === 'hours') {
                const an = parseFloat(av);
                const bn = parseFloat(bv);
                const ai = isNaN(an) ? (asc ? Infinity : -Infinity) : an;
                const bi = isNaN(bn) ? (asc ? Infinity : -Infinity) : bn;
                return asc ? ai - bi : bi - ai;
            }
            return asc ? av.localeCompare(bv) : bv.localeCompare(av);
        });
        rows.forEach(function (r) { tbody.appendChild(r); });
    }

    document.querySelectorAll('th.sortable').forEach(function (th) {
        th.addEventListener('click', function () {
            sortTable(th, th.dataset.asc !== 'true');
        });
    });

    // Default: sort every table by price ascending
    document.querySelectorAll('th[data-col="price"]').forEach(function (th) {
        sortTable(th, true);
    });

    // Default: deal filter starts enabled
    document.querySelectorAll('tbody tr').forEach(function (tr) {
        var pcPrice = parseFloat(tr.dataset.pcPrice || '');
        var priceTd = tr.querySelector('td[data-price]');
        var price = parseFloat(priceTd ? priceTd.dataset.price : '');
        tr.classList.toggle('hidden-by-deal', isNaN(pcPrice) || price >= pcPrice);
    });
    updateGameVisibility();
});
"""


def _hours_left(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        end = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return (end - datetime.now(timezone.utc)).total_seconds() / 3600
    except ValueError:
        return None


def _fmt_end(ts: str | None) -> tuple[str, bool, float]:
    """Returns (display_str, is_ending_soon, hours_for_sort)."""
    hours = _hours_left(ts)
    if hours is None:
        return "—", False, 9999.0   # BIN: no end time; sort to end
    soon = hours < 6
    if hours < 1:
        return f"{int(hours * 60)}m", soon, hours
    if hours < 24:
        return f"{hours:.1f}h", soon, hours
    return f"{int(hours // 24)}d {int(hours % 24)}h", soon, hours


def _effective_price(row: dict) -> float | None:
    """Item price plus shipping, i.e. the actual all-in cost to compare against
    PriceCharting. Unknown shipping (local pickup/freight, no shippingOptions
    returned) is treated as 0 here — a listing with genuinely unknown shipping
    shouldn't be excluded from ranking, just flagged in the UI (see _JS/_CSS
    ship-note styling)."""
    price = row.get("price")
    if price is None:
        return None
    return price + (row.get("shipping_price") or 0)


def _cheapest_n(rows: list[dict], n: int) -> list[dict]:
    return sorted(rows, key=lambda r: (_effective_price(r) is None, _effective_price(r) or 0))[:n]


def generate(listings: list[dict], games: list[dict], limit_per_game: int = 15, new_ids: set[str] = frozenset()) -> Path:
    by_game: dict[str, list[dict]] = defaultdict(list)
    for lst in listings:
        by_game[lst["game_name"]].append(lst)

    by_game = {k: _cheapest_n(v, limit_per_game) for k, v in by_game.items()}

    trimmed = [lst for rows in by_game.values() for lst in rows]
    auction_count = sum(1 for l in trimmed if l.get("buying_option") == "AUCTION")
    bin_count = len(trimmed) - auction_count
    games_with = sum(1 for g in games if g["name"] in by_game)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    summary_html = """<div class="summary">
  <div class="stat"><div class="n">{gw}/{gt}</div><div class="label">Games with listings</div></div>
  <div class="stat"><div class="n">{ac}</div><div class="label">Active auctions</div></div>
  <div class="stat"><div class="n">{bc}</div><div class="label">Buy It Now</div></div>
</div>""".format(gw=games_with, gt=len(games), ac=auction_count, bc=bin_count)

    legend_html = """<div class="legend">
  <strong>Filter:</strong>
  <button class="legend-filter" data-filter="deal"><span class="badge deal">📉 Bargain</span> - Below PC value (price + shipping)</button>
  <button class="legend-filter" data-filter="auction"><span class="badge auction">🔨 Auction</span> - Active bid with end time</button>
  <button class="legend-filter" data-filter="bin"><span class="badge bin">🛒 BIN</span> - Buy It Now</button>
  <button class="legend-filter off" data-filter="new"><span class="new-badge">✦ New</span> - New listings</button>
</div>"""

    filter_html = """<div class="filter-box">
  <label for="game-filter">Filter by game:</label>
  <input id="game-filter" type="search" placeholder="e.g. Bubble Bobble" autocomplete="off">
</div>"""

    game_sections = []
    for game in games:
        rows = by_game.get(game["name"])
        if not rows:
            continue
        pc = (f'<span class="pc-price">'
              f'<img class="pc-icon" src="data:image/png;base64,{_PC_ICON_B64}" alt="PriceCharting">'
              f': ${game["list_price"]:.2f}</span>') if game.get("list_price") else ""
        auction_cnt = sum(1 for r in rows if r.get("buying_option") == "AUCTION")
        bin_cnt = len(rows) - auction_cnt
        has_new = any(r.get("item_id") in new_ids for r in rows)
        new_header = '<span class="new-badge">✦ New</span>' if has_new else ""
        count_badges = (
            f'<span class="count-badges">'
            f'{new_header}'
            f'<span class="badge auction">🔨 {auction_cnt}</span>'
            f'<span class="badge bin">🛒 {bin_cnt}</span>'
            f'</span>'
        )
        prices = [p for r in rows if (p := _effective_price(r)) is not None]
        if prices:
            lo, hi = min(prices), max(prices)
            ebay_range = (f'<span class="ebay-range">'
                          f'<img style="width: 24px; height: 24px" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAEZ0lEQVR4nO2WX2jdVBzHz+aaU6Xq/FNMWv+AMB8cDsTmTGR4WXKRm1x1ylD2uJcNhvgwbaIy9O7BP7s3iopubDBa+uJkIlYHZTCk5yS3ndauM1nV4r9R0I1NurVN3LR//En+3Ztbs84nbSEfOC/n/BK+39+fkyCUkZGRkZGRkZGRkfFfIegO+IvXnOfRckTIDPzPCEvVwNTGjodcmXR7MhlzJeJ5Epn0JNHxJLJvWiL3phlo10bWCLqzV9Cc04LuzAi6PSVoDhN0exvaPtyUfD+YLa3A8B5geAQYngSK54FyZ4BxFlBuV7e5YYthqRAsU31lMa0VS/kiiqXBhieLL7sy+cuTCXiy+ENgRCJ7PYlU/X1XFmc9SdyaNCDoNuU1+zKvOxd53f6E1+yDguZ8Lmj2fHCu2UP8SyOtgXgL3w2MOwsMAzD8BzD8GTDuADD8KTB8Mdin3Jke6+EvI2GTb/dvWp0mvlwtqLHRclXd6IsvhMIJuJL4OpTQyuQDv0vik64kzvnLkzvurxsIqtB787Pf35CMv00/SXjdnghNOAwhWAGM6wlF4ikwuXsaKtPfcitQbtw/99j11atVwbCUwGTFUgaCDVcmfVHmvwGEVqQ95MniR1HMBzUDmnO+tTTakhYvaM72WlznqUcWawcfoNx7kcELFVPti6vwhlW8CSUom8qjscGKVcwHm55MfgvESaTqSeILacuVyJGgQjI5m6hAN7oCbS9+e4ugO3NRKxmBSLaKAMUGUI4B5c4Dw7NRSzWsillYZ5jKfCDSVEvJ91ZMdSisjjJY23RlMhO30NWWPw+19tHtXWgReN35xY+7Uz/RA4zrqomk+AJQ7ihQ7v1oqPcEgxydB0It5dDCKhhW4bFa9quFelU9SZwIxYll9C+o97/ddaUYfy54zf7Tj3v34I6+RIZfg1HELYyH0EzNQJkW11RMdSYUrOxOZr9iqscbHnYlsTccYPIT5HKr0gS5eVF2JfLUdL4jl2ihc0Jp+Lp0k/a2OG70yNreSNwsHEbX/EM8oJXA8HdJAz6GqeyPq1Bh6tbacFuK0vCC6fz6Da5E5qM52LfQxLS8fnN4AwXnpYZbSLc/vH3n4LXJeF5zcv7VGl21X82x5s56BbhNKeLLyRmIz94aLLZXTOVSJHw2yv5QWsLQdF7cEc+CK5FxVxa7PFl8x5MJq1+x5Cjkcs118c6x8OPlnBN057DfUoLmHE+cj7U9d+oOOIZuBIrHov6fj+7+V4Fy+4FxPwLFM0DxoYUGgipYarmeeRUMphZTDYRt8uB9wcdLJqP+V9iVxUu+GU8iH7t58en4+xALbNO/3tLe6azzhfOaPR5/iXnNHuA1e2eyvaAfrQaGdwPFJ4DiCWD4MlDuZ6BcN1hNa6EfF1INDKh31a9NZRgg/ZpfshhM1WIDb1aLj6PlRKk/12yYyq/RvX9y2WW/YinP1LJvKk+g5cSB4QeaDEs9Hf0TjZag1PB/lpGRkZGRkZGRkYGWBH8DfxaCHN6MsZMAAAAASUVORK5CYII=" alt="ebay">'
                          f': ${lo:.2f}{"&nbsp;–&nbsp;$" + f"{hi:.2f}" if hi != lo else ""}</span>')
        else:
            ebay_range = ""
        trs = []
        for r in rows:
            opt = r.get("buying_option", "")
            row_type = "auction" if opt == "AUCTION" else "bin"
            is_new = r.get("item_id") in new_ids
            type_badge = '<span class="badge auction">🔨 Auction</span>' if opt == "AUCTION" else '<span class="badge bin">🛒 BIN</span>'
            new_row_badge = ' <span class="new-badge">✦ New</span>' if is_new else ""
            badge = f"{type_badge}{new_row_badge}"
            price_val = r.get("price")
            shipping_val = r.get("shipping_price")
            effective_val = _effective_price(r)
            price_attr = f'{effective_val:.2f}' if effective_val is not None else "9999"
            price_disp = f'${price_val:.2f}' if price_val is not None else "—"
            if shipping_val is None and r.get("shipping_cost_type") == "CALCULATED":
                # eBay's API frequently can't price CALCULATED shipping (errorId
                # 11510) even with a buyer zip supplied - not a fetch failure.
                ship_note = ' <span class="ship-note unknown">+ ship: calc.</span>'
            elif shipping_val is None:
                ship_note = ' <span class="ship-note unknown">+ ship?</span>'
            elif shipping_val > 0:
                ship_note = f' <span class="ship-note">+ ${shipping_val:.2f} ship</span>'
            else:
                ship_note = ' <span class="ship-note free">+ free ship</span>'
            list_price = game.get("list_price")
            price_cls = " good-deal" if (effective_val is not None and list_price and effective_val < list_price) else ""
            bids = f' <span style="color:#999;font-size:.8rem">({r["bid_count"]} bids)</span>' if r.get("bid_count") else ""
            img = f'<img class="thumb" src="{r["image_url"]}">' if r.get("image_url") else ""
            cond = r.get("condition") or "—"
            end_str, soon, hours_val = _fmt_end(r.get("end_time"))
            end_cls = ' class="ending-soon"' if soon else ""
            pc_attr = f'{list_price:.2f}' if list_price is not None else ""
            trs.append(
                f'<tr data-type="{row_type}" data-pc-price="{pc_attr}" data-new="{"true" if is_new else "false"}">'
                f'<td>{img}</td>'
                f'<td data-label="Type">{badge}</td>'
                f'<td data-label=""><a href="{r.get("url", "#")}" target="_blank">{r.get("title", "")}</a></td>'
                f'<td data-label="Price" data-price="{price_attr}" class="price{price_cls}">{price_disp}{ship_note}{bids}</td>'
                f'<td data-label="Cond." data-condition="{cond}">{cond}</td>'
                f'<td data-label="Seller">{r.get("seller") or "—"}</td>'
                f'<td data-label="Ends" data-hours="{hours_val:.2f}"{end_cls}>{end_str}</td>'
                f'</tr>'
            )
        game_sections.append(f"""<details class="game">
  <summary><h2>{game["name"]}</h2>{pc}{ebay_range}{count_badges}</summary>
  <div class="game-body">
    <table>
      <thead><tr>
        <th></th><th>Type</th><th>Title</th>
        <th class="sortable" data-col="price">Price</th>
        <th class="sortable" data-col="condition">Condition</th>
        <th>Seller</th>
        <th class="sortable" data-col="hours">Ends In</th>
      </tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table>
  </div>
</details>""")

    missing = [g["name"] for g in games if g["name"] not in by_game]
    missing_section = ""
    if missing:
        items_html = "".join(f"<li>{n}</li>" for n in missing)
        missing_section = f"""<div class="no-listings">
  <h3>No current listings found for:</h3>
  <ul>{items_html}</ul>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>eBay NES Game Tracker</title>
<style>{_CSS}</style></head>
<body>
<h1>
  <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAABg0lEQVR4nO3Yv0rDUBQG8KCDgz6AjtnsG+iaSd9AZxcjdOq5RacsQn0C9Q10dapLZx3d/LN8B0TaLNk61iuFikVC7r1pI0c4H3xDA5eeX+4NKY0ijUaj0WhKwsxbzGyX3TiOK8slawBsRqEBsC8IsFcHcCYIcBoMYObbJgCDwaCyXL7upg7gRRDgOWj44XC4DmAiBQBgkuf5hjcAwG4Twy+wAxbATgggFQg49gYw87U0ADNfhQAeBQIevIa31q4CGEsDABhPZ3MCALSaGn7BHbAAtn0AhyFfGNo6b2L+ARz4AC6kApi55wQw830ZYFlHaEFA3wcwEgzInYCiKOx8vwG/r9dtkiSVLRzrFfB2knpVAYUeoeJ/Aowxtsm6AKZiLRF9OAFENBEMePcB3DUNmP7onTaZDT3/2bH+0gnodDqJz51zXW8A8NntdltOwGwXngQC+l7Dz3bhSNoRIiL/f+fa7fYaEY0EPcSvWZatRCExxpxLARBRGjS8RqPRaDSa6G/yBXY7jBJLE1gkAAAAAElFTkSuQmCC" alt="nintendo-entertainment-system">
  eBay NES Game Tracker
</h1>
<p class="meta">Generated: {now_str} &mdash; showing up to {limit_per_game} cheapest listings per game</p>
<div class="top-controls">
{summary_html}
{filter_html}
{legend_html}
</div>
{"".join(game_sections)}
{missing_section}
<script>{_JS}</script>
</body></html>"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html)
    return OUTPUT
