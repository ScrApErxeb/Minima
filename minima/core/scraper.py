import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from minima.core.logger import logger
from minima.core.config_loader import get


class Scraper:
    def __init__(self):
        self.headers = get("headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; MinimaBot/0.9)",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.timeout = int(get("timeout", 10))
        self.max_workers = int(get("max_workers", 5))
        self.retries = int(get("retries", 3))

    def fetch_preview(self, url: str, max_chars: int = 5000) -> str:
        """Récupère seulement un extrait du HTML pour détecter la langue."""
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout, stream=True)
            resp.raise_for_status()
            preview = ""
            for chunk in resp.iter_content(chunk_size=1024, decode_unicode=True):
                preview += chunk
                if len(preview) >= max_chars:
                    break
            logger.info(f"Preview fetched {url} ({len(preview)} chars)")
            return preview
        except requests.RequestException as e:
            logger.warning(f"Échec du preview pour {url}: {e}")
            return ""

    def fetch_html(self, url: str):
        """Télécharge une page avec gestion de retry."""
        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.get(url, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200:
                    logger.info(f"Fetched {url} ({resp.status_code})")
                    return resp.text
                elif resp.status_code in (403, 429):
                    logger.warning(f"{url} -> HTTP {resp.status_code}, tentative {attempt}/{self.retries}")
                    time.sleep(2 * attempt)
                else:
                    logger.warning(f"{url} -> HTTP {resp.status_code}")
                    break
            except requests.RequestException as e:
                logger.warning(f"{url} -> tentative {attempt}/{self.retries} échouée: {e}")
                time.sleep(1)
        logger.warning(f"Échec définitif pour {url}")
        return None

    def fetch_all(self, urls: list[str]) -> dict[str, str | None]:
        """Télécharge plusieurs URLs en parallèle."""
        results = {}
        start = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.fetch_html, url): url for url in urls}
            for future in as_completed(futures):
                url = futures[future]
                results[url] = future.result()

        duration = round(time.time() - start, 2)
        rps = round(len(urls) / duration, 2) if duration > 0 else 0
        logger.info(f"Fetch terminé ({len(urls)} URLs en {duration}s, {rps} RPS)")
        return results
