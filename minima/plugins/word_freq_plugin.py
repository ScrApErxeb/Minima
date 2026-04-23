import collections
import re
from bs4 import BeautifulSoup
from minima.core.logger import logger

# Liste de mots à ignorer (à compléter pour filtrer le bruit restant)
STOPWORDS = {"le", "la", "les", "des", "du", "un", "une", "et", "en", "est", "pour", "dans"}

def process(url, html):
    """Analyse la fréquence des mots dans le contenu principal de la Présidence."""
    soup = BeautifulSoup(html, "html.parser")

    # 1. Nettoyage radical du bruit technique
    for tag in soup(["script", "style", "noscript", "svg", "canvas", "iframe"]):
        tag.decompose()

    # 2. CIBLAGE PRÉCIS : On cherche ta balise spécifique
    # On ajoute "entry-content" au cas où certaines pages varient
    content_area = soup.find("div", class_="post-entry-content") or \
                   soup.find("div", class_="entry-content") or \
                   soup.find("article")

    if not content_area:
        logger.warning(f"Zone de contenu non trouvée pour {url}")
        return {"top_words": {}}

    # 3. Extraction du texte uniquement dans les paragraphes et titres de cette zone
    text_parts = []
    for tag in content_area.find_all(['p', 'h1', 'h2', 'h3']):
        text_parts.append(tag.get_text())
    
    full_text = " ".join(text_parts).lower()

    # 4. Nettoyage des caractères spéciaux et comptage
    words = re.findall(r'\b[a-z]{3,}\b', full_text) # Mots de 3 lettres min
    filtered_words = [w for w in words if w not in STOPWORDS]
    
    counter = collections.Counter(filtered_words)
    top_10 = dict(counter.most_common(10))

    return {"top_words": top_10}