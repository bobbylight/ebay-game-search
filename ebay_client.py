import base64
import time
import requests

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
SCOPE = "https://api.ebay.com/oauth/api_scope"


class EbayClient:
    def __init__(self, app_id: str, cert_id: str, buyer_zip: str | None = None):
        self._app_id = app_id
        self._cert_id = cert_id
        self._buyer_zip = buyer_zip
        self._token: str | None = None
        self._token_expiry: float = 0

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token
        creds = base64.b64encode(f"{self._app_id}:{self._cert_id}".encode()).decode()
        resp = requests.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials", "scope": SCOPE},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data["expires_in"]
        return self._token

    def search_game(self, name: str, platform: str = "NES", limit: int = 25) -> list[dict]:
        """Search for a game, returning both AUCTION and FIXED_PRICE listings.

        Restricting to category 139973 (Video Games & Consoles) plus the platform
        in the query string reduces noise from guides, cases, and repros.
        If non-game items are still too common, we can add a Claude classification
        step here to verify each listing title refers to the actual cartridge.
        """
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }
        if self._buyer_zip:
            # Without this, eBay estimates CALCULATED shipping to a generic
            # default location instead of the buyer's actual zip.
            headers["X-EBAY-C-ENDUSERCTX"] = f"contextualLocation=country=US,zip={self._buyer_zip}"

        resp = requests.get(
            BROWSE_URL,
            headers=headers,
            params={
                "q": f"{name} {platform}",
                "category_ids": "139973",
                "limit": limit,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("itemSummaries", [])
