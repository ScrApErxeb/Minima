import os
import time
import yaml
import signal
from urllib.parse import urljoin, urlparse

from minima.core.logger import logger
from minima.core.queue import PersistentQueue
from minima.core.scraper import Scraper
from minima.core.generic_analyzer import GenericAnalyzer
from minima.core.exporter import Exporter
from minima.core.config_loader import ensure_paths
from minima.core.errors import MinimaError
from minima.plugins.plugin_validator import validate_all

# --- Configuration des Chemins ---
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/config.yaml"))
QUEUE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/queue.json"))
PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "plugins"))

def normalize_url(url: str) -> str:
    """Nettoie l'URL pour éviter les doublons techniques."""
    parsed = urlparse(url)
    # On garde le schéma, le netloc et le path, on vire les fragments (#) et les query params si besoin
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if normalized.endswith("/") and len(parsed.path) > 1:
        normalized = normalized[:-1]
    return normalized.lower().strip()

def load_config(config_path=None):
    config_file = config_path or CONFIG_PATH
    if not os.path.exists(config_file):
        logger.warning(f"Config non trouvée : {config_file}")
        return {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Erreur config : {e}")
        return {}

def main(config_path: str = None):
    logger.info("=== MINIMA V1.0 : LANCEMENT OFFICIEL ===")
    try:
        ensure_paths()
        cfg = load_config(config_path)

        # Paramètres
        mode = cfg.get("mode", "scrap")
        max_depth = int(cfg.get("max_depth", 1))
        delay = cfg.get("delay", 0)
        accepted_languages = cfg.get("accepted_languages", ["en", "fr"])
        export_flush_every = int(cfg.get("export_flush_every", 10))

        # Initialisation
        valid_plugins = validate_all(PLUGIN_DIR)
        queue = PersistentQueue(QUEUE_PATH)
        analyzer = GenericAnalyzer(logger=logger)
        exporter = Exporter(flush_every=export_flush_every)
        scraper = Scraper()

        # URLs de départ avec normalisation
        for url in cfg.get("urls", []):
            queue.add({"url": normalize_url(url), "depth": 0, "score": 0})

        # Gestion interruption
# --- Gestion interruption (PLACER JUSTE AVANT LA BOUCLE WHILE) ---
        def handle_sigint(sig, frame):
            # Utilisation de print pour un feedback visuel immédiat
            print("\n" + "!"*30)
            print("  INTERRUPTION DÉTECTÉE (Ctrl+C)")
            print("  Sauvegarde finale des données...")
            print("!"*30)
            
            try:
                exporter.flush()
                print("✅ Données exportées avec succès.")
            except Exception as e:
                print(f"❌ Erreur lors du flush final : {e}")
            
            print("👋 Arrêt de Minima. À bientôt !")
            # On utilise os._exit pour tuer tous les threads immédiatement
            os._exit(0)

        signal.signal(signal.SIGINT, handle_sigint)
        
        # Boucle de traitement
        while not queue.is_empty():
            items_to_fetch = queue.remaining_urls()
            if not items_to_fetch: break

            # Récupération groupée
            html_map = scraper.fetch_all([item["url"] for item in items_to_fetch])

            for item in items_to_fetch:
                url, depth = item["url"], item["depth"]
                html = html_map.get(url)

                if not html:
                    queue.mark_processed(item)
                    continue

                # Filtrage langue
                lang = analyzer.detect_language(html)
                if lang not in accepted_languages:
                    logger.info(f"Ignoré (Langue {lang}) : {url}")
                    queue.mark_processed(item)
                    continue

                # Analyse technique + Plugins
                result = analyzer.analyze(html, url)
                result['score'] = item.get('score', 0)

                for plugin in valid_plugins:
                    try:
                        if hasattr(plugin, "process"):
                            p_res = plugin.process(url, html)
                            if p_res: result.update(p_res)
                    except Exception as e:
                        logger.warning(f"Erreur plugin {getattr(plugin, '__name__', 'plg')} : {e}")

                # Fin de traitement & Export
                queue.mark_processed(item)
                exporter.add_results([result])
                logger.info(f"OK ({lang}) : {url}")

                # Découverte de liens & Déduplication
                if "crawl" in mode and depth < max_depth:
                    for link in result.get("links", []):
                        full_url = normalize_url(urljoin(url, link))
                        # La queue gère déjà le 'if full_url not in processed' en interne
                        queue.add({"url": full_url, "depth": depth + 1, "score": 0})

                if delay > 0: time.sleep(delay)

        exporter.flush()
        logger.info("=== TRAVAIL TERMINÉ ===")

    except Exception as e:
        logger.exception(f"Erreur fatale : {e}")

if __name__ == "__main__":
    main()