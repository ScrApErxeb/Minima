from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # pour résultats reproductibles

class GenericAnalyzer:
    def __init__(self, logger=None):
        self.logger = logger

    def analyze(self, html, url):
        """Analyse basique du contenu HTML"""
        try:
            soup = BeautifulSoup(html, "lxml")
            title = soup.title.string.strip() if soup.title else "Sans titre"
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            images = [img.get("src") for img in soup.find_all("img", src=True)]
            result = {
                "url": url,
                "title": title,
                "links": links,
                "images": images,
                "link_count": len(links),
                "image_count": len(images),
            }
            if self.logger:
                self.logger.info(f"Analyse terminée pour {url}")
            return result
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Échec de l’analyse pour {url}: {e}")
            return {"url": url, "error": str(e)}

    def detect_language(self, html):
        """Détecte la langue du contenu HTML"""
        try:
            text = self.extract_text(html)
            return detect(text)
        except Exception:
            return "unknown"

    def extract_text(self, html):
        """Extrait le texte brut du HTML"""
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)
