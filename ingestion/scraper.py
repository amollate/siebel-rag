import logging
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SiebelDocScraper:
    def __init__(self, base_url="", max_pages=50, delay=1.0):
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
        self.visited = set()
        self.to_visit = [base_url]
        self.collected = []

    def fetch_page(self, url):
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            return None

    def extract_text(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(base_url, href)
            parsed = urlparse(full)
            if parsed.scheme in ("http", "https"):
                links.add(full)
        return links

    def is_relevant(self, url):
        lower = url.lower()
        keywords = ["siebel", "crm", "oracle", "business component", "applet",
                     "view", "workflow", "business service", "integration",
                     "architecture", "configuration", "tutorial", "guide",
                     "documentation", "fundamentals", "installation"]
        return any(kw in lower for kw in keywords)

    def crawl(self):
        while self.to_visit and len(self.collected) < self.max_pages:
            url = self.to_visit.pop(0)
            if url in self.visited:
                continue
            self.visited.add(url)

            logger.info("Crawling: %s", url)
            html = self.fetch_page(url)
            if html is None:
                continue

            text = self.extract_text(html)
            if len(text) > 200:
                self.collected.append({"url": url, "content": text})
                logger.info("Collected %d chars from %s", len(text), url)

            links = self.extract_links(html, url)
            for link in links:
                if link not in self.visited and self.is_relevant(link):
                    self.to_visit.append(link)

            time.sleep(self.delay)

        logger.info("Crawling complete. Collected %d pages.", len(self.collected))
        return self.collected