import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from minima.core.logger import logger
from minima.core.config_loader import get

class Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = get("headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; MinimaBot/0.9)",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.session.headers.update(self.headers)
        self.timeout = int(get("timeout", 10))
        self.max_workers = int(get("max_workers", 5))
        self.retries = int(get("retries", 3))

        # --- AJOUT : Extensions à ignorer ---
        self.excluded_ext = (
            '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', 
            '.mp4', '.mp3', '.docx', '.xlsx', '.pptx', '.exe'
        )

    def fetch_html(self, url: str):
        """Télécharge la page SEULEMENT si c'est du contenu textuel."""
        
        # 1. Vérification rapide par l'URL
        if url.lower().endswith(self.excluded_ext):
            logger.info(f"Ignoré (Fichier média) : {url}")
            return None

        for attempt in range(1, self.retries + 1):
            try:
                # On utilise stream=True pour vérifier le header avant de tout télécharger
                resp = self.session.get(url, timeout=self.timeout, stream=True)
                
                if resp.status_code == 200:
                    # 2. Vérification de sécurité par le Content-Type
                    content_type = resp.headers.get('Content-Type', '').lower()
                    if 'text/html' not in content_type:
                        logger.warning(f"Ignoré (Format non-HTML: {content_type}) : {url}")
                        return None
                    
                    # On récupère le texte seulement si c'est du HTML
                    return resp.text
                
                elif resp.status_code in (403, 429):
                    logger.warning(f"Tentative {attempt} : Blocage {resp.status_code}")
                    time.sleep(2 * attempt)
                else:
                    break
            except requests.RequestException as e:
                logger.debug(f"Erreur réseau sur {url} : {e}")
                time.sleep(1)
        return None
        
    def fetch_preview(self, url: str, max_chars: int = 5000) -> str:
            """Récupère seulement un extrait du HTML pour détecter la langue."""
            try:
                resp = requests.get(url, headers=self.headers, timeout=self.timeout, stream=True)
                resp.raise_for_status()
                
                # Forcer l'encodage si requests ne le trouve pas (évite les erreurs de décodage)
                if resp.encoding is None:
                    resp.encoding = 'utf-8'

                preview = ""
                # Utilisation de iter_decode pour être sûr d'avoir du texte (str)
                for chunk in resp.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk:
                        # Sécurité : Si le chunk est quand même en bytes, on le décode manuellement
                        if isinstance(chunk, bytes):
                            chunk = chunk.decode(resp.encoding, errors='ignore')
                        
                        preview += chunk
                        
                    if len(preview) >= max_chars:
                        break
                
                logger.info(f"Preview fetched {url} ({len(preview)} chars)")
                return preview
            except requests.RequestException as e:
                logger.warning(f"Échec du preview pour {url}: {e}")
                return ""

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
