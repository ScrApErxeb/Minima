import collections
import re
from bs4 import BeautifulSoup
from minima.core.logger import logger

# On définit les cibles ici, dans le plugin
SMART_TARGETS = [
    {"name": "Presidence/WP Custom", "class": "post-entry-content"},
    {"name": "WordPress Standard", "class": "entry-content"},
    {"name": "Article Universel", "tag": "article"},
    {"name": "Contenu Principal", "tag": "main"}
]

STOPWORDS = {"le", "la", "les", "des", "du", "un", "une", "et", "en", "est", "pour", "dans", "par", "qui", "que", "sur", "aux"}

def find_content_zone(soup):
    """Trouve la zone de texte utile au milieu du HTML complet."""
    for target in SMART_TARGETS:
        result = None
        if "class" in target:
            result = soup.find(class_=target["class"])
        elif "tag" in target:
            result = soup.find(target["tag"])
        
        if result:
            return result
    return soup.body or soup # Fallback si rien n'est trouvé

def process(url, html):
    """Analyse chirurgicale de la fréquence des mots."""
    if not html:
        return {"top_words": {}}

    soup = BeautifulSoup(html, "html.parser")

    # 1. Nettoyage du bruit technique (uniquement pour l'analyse)
    for noise in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer"]):
        noise.decompose()

    # 2. On cible la zone de contenu pour éviter les menus/sidebar
    content_area = find_content_zone(soup)

    # 3. Extraction du texte (Titres, Paragraphes, Listes)
    text_parts = [tag.get_text() for tag in content_area.find_all(['p', 'h1', 'h2', 'h3', 'li'])]
    full_text = " ".join(text_parts).lower()

    # 4. Nettoyage des chiffres (évite janv1, fév2) et ponctuation
    full_text = re.sub(r'\d+', ' ', full_text)
    
    # 5. Extraction et filtrage
    words = re.findall(r'\b[a-z]{3,}\b', full_text)
    filtered_words = [w for w in words if w not in STOPWORDS]
    
    counter = collections.Counter(filtered_words)
    return {"top_words": dict(counter.most_common(10))}