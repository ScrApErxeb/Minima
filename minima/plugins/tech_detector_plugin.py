import re
from bs4 import BeautifulSoup
from minima.core.logger import logger

def process(url, html):
    """Détecte les technologies CMS et Analytics sans bloquer le crawl."""
    if not html:
        return {"tech_stack": "unknown"}

    soup = BeautifulSoup(html, "html.parser")
    techs = []
    
    # --- 1. DÉTECTION CMS ---
    # Recherche de WordPress
    if soup.find("meta", attrs={"name": "generator", "content": re.compile(r"WordPress", re.I)}) \
       or "/wp-content/" in html or "/wp-includes/" in html:
        techs.append("WordPress")
    
    # Recherche de Shopify
    if "shopify-pay" in html or "/cdn.shopify.com/" in html:
        techs.append("Shopify")

    # --- 2. DÉTECTION ANALYTICS / TRACKING ---
    if "googletagmanager.com" in html or "google-analytics.com" in html:
        techs.append("Google Analytics/GTM")
    
    if "facebook.net/en_US/fbevents.js" in html:
        techs.append("Facebook Pixel")

    # --- 3. DÉTECTION FRAMEWORKS CSS/JS ---
    if "bootstrap" in html.lower():
        techs.append("Bootstrap")
    if "tailwind" in html.lower():
        techs.append("Tailwind CSS")
    if "react" in html.lower() or "__next" in html:
        techs.append("React/Next.js")

    # On retourne un dictionnaire propre
    return {
        "technologies": list(set(techs)) if techs else ["Unknown"],
        "is_wordpress": "WordPress" in techs
    }