import requests

_NTFY_URL = "https://ntfy.sh"


def send(topic: str, title: str, body: str, url: str | None = None) -> bool:
    headers = {"Title": title}
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
