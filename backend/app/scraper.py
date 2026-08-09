"""Web scraper: fetch a URL (optionally crawling same-domain pages) and persist
extracted content as markdown files in the scraped corpus directory."""
import ipaddress
import logging
import os
import re
import socket
import time
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup

from app.config import SCRAPED_DIR, SCRAPE_TIMEOUT, SCRAPE_MAX_PAGES, SCRAPE_USER_AGENT
from app.uploads import unique_path

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = {"http", "https"}
MAX_CONTENT_CHARS = 200_000

_client = httpx.Client(
    timeout=SCRAPE_TIMEOUT,
    follow_redirects=True,
    headers={"User-Agent": SCRAPE_USER_AGENT},
)

# Tags that carry no useful page content.
_NOISE_TAGS = ["script", "style", "nav", "footer", "aside", "form", "iframe", "noscript"]


def _hostname_is_private(hostname: str | None) -> bool:
    """Reject local/private network targets (basic SSRF protection)."""
    if not hostname:
        return True
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(hostname, None)
    except OSError:
        return True
    return any(
        ipaddress.ip_address(addr[4][0]).is_private
        or ipaddress.ip_address(addr[4][0]).is_loopback
        for addr in infos
    )


def _validate_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise ValueError("URL must start with http:// or https:// and include a host")
    if _hostname_is_private(parsed.hostname):
        raise ValueError("URL points to a private or local network address")
    return url


def _fetch(url: str) -> str | None:
    try:
        resp = _client.get(url)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as e:
        logger.warning(f"Fetch failed for {url}: {e}")
        return None


def _extract_page(url: str, html: str) -> tuple[str | None, str | None]:
    """Extract (title, text). Uses trafilatura, falling back to BeautifulSoup."""
    title = None
    try:
        meta = trafilatura.extract_metadata(html, default_url=url)
        if meta:
            title = meta.title
    except Exception:
        pass

    text = trafilatura.extract(html, url=url, include_comments=False, include_tables=True)
    # trafilatura is built for article-shaped pages; for docs/landing pages it
    # can return almost nothing, so fall back to a container-aware soup parse.
    if not text or len(text.strip()) < 500:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(_NOISE_TAGS):
            tag.decompose()
        if not title and soup.title and soup.title.string:
            title = soup.title.string.strip()
        container = (
            soup.find("main")
            or soup.find(attrs={"role": "main"})
            or soup.find("article")
            or soup.find(id="content")
            or soup.body
        )
        text = container.get_text("\n", strip=True) if container else ""

    if not text or not text.strip():
        return None, ""
    text = text.strip()
    if len(text) > MAX_CONTENT_CHARS:
        text = text[:MAX_CONTENT_CHARS] + "\n...[truncated]"
    title = (title or "").strip() or url
    return title, text


def _same_domain_links(html: str, base: str, domain: str) -> list[str]:
    """Collect http(s) links pointing back at the same hostname."""
    links = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            absolute = urljoin(base, href)
            parsed = urlparse(absolute)
            if parsed.scheme in ALLOWED_SCHEMES and parsed.netloc == domain:
                links.append(absolute)
    except Exception:
        pass
    return links


def _save_page(url: str, title: str, text: str) -> str:
    """Write the page to the scraped corpus as a markdown file with source metadata."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", urlparse(url).netloc + "-" + title).strip("-").lower()
    if len(slug) > 90:
        slug = slug[:90].rstrip("-")
    if not slug:
        slug = f"page-{int(time.time())}"

    os.makedirs(SCRAPED_DIR, exist_ok=True)
    path = unique_path(SCRAPED_DIR, slug + ".md")

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"source_url: {url}\n\n# {title}\n\n{text}\n")
    logger.info(f"Saved scraped page {os.path.basename(path)} from {url}")
    return os.path.basename(path)


def scrape_url(url: str, max_pages: int = 1) -> dict:
    """Scrape a URL and up to max_pages - 1 same-domain linked pages.

    Returns {"saved": [filenames], "skipped": [{url, reason}], "pages": n}.
    """
    url = _validate_url(url)
    domain = urlparse(url).netloc
    max_pages = max(1, min(int(max_pages), SCRAPE_MAX_PAGES))

    queue = [url]
    seen: set[str] = set()
    saved: list[str] = []
    skipped: list[dict] = []

    while queue and len(saved) < max_pages:
        page = queue.pop(0)
        if page in seen:
            continue
        seen.add(page)

        html = _fetch(page)
        if not html:
            skipped.append({"url": page, "reason": "request failed or non-HTML response"})
            continue

        title, text = _extract_page(page, html)
        if not text:
            skipped.append({"url": page, "reason": "no extractable content"})
            continue

        saved.append(_save_page(page, title, text))

        if len(saved) < max_pages:
            for link in _same_domain_links(html, page, domain):
                if link not in seen:
                    queue.append(link)

    return {"saved": saved, "skipped": skipped, "pages": len(saved)}
