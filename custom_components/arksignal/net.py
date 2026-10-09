"""Posting to the ArkSignal upload address, following redirects the right way.

A site that answers plain http with a permanent redirect to https (nearly every site does) would turn a POST into a GET if the redirect were followed automatically, and the upload
address only takes POST. So the redirect is followed by hand, repeating the POST with the same body at the new address, and the final address is remembered."""
from __future__ import annotations

from urllib.parse import urljoin

REDIRECTS = (301, 302, 303, 307, 308)


async def post_following(session, url: str, payload: dict, timeout: int = 20, hops: int = 3):
    """POST `payload` as JSON. Returns (status, final url); status 0 when it ran out of redirects."""
    for _ in range(hops + 1):
        async with session.post(url, json=payload, timeout=timeout, allow_redirects=False) as resp:
            where = resp.headers.get("Location")
            if resp.status in REDIRECTS and where:
                url = urljoin(url, where)
                continue
            return resp.status, url
    return 0, url
