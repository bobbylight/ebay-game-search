import requests

_NTFY_URL = "https://ntfy.sh"
_ICON_URL = "https://raw.githubusercontent.com/bobbylight/ebay-game-search/refs/heads/main/img/nes-48x48.png"


def send(topic: str, title: str, body: str, url: str | None = None) -> bool:
    headers = {"Title": title, "Icon": _ICON_URL}
    if url:
        headers["Click"] = url
    try:
        resp = requests.post(
            f"{_NTFY_URL}/{topic}",
            data=body.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        return resp.ok
    except Exception:
        return False
