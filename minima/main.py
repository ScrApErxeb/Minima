import os
import time
import yaml
from urllib.parse import urljoin

from minima.core.logger import logger
from minima.core.queue import PersistentQueue
from minima.core.scraper import Scraper
from minima.core.generic_analyzer import GenericAnalyzer
from minima.core.exporter import Exporter
from minima.core.config_loader import ensure_paths
from minima.core.errors import MinimaError
from minima.plugins.plugin_validator import validate_all

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/config.yaml"))
QUEUE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/queue.json"))
PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "plugins"))

def load_config(config_path=None):
    config_file = config_path or CONFIG_PATH
    logger.info(f"Tentative de chargement du fichier de config: {config_file}")
    if not os.path.exists(config_file):
        logger.warning(f"Config file not found: {config_file}")
        return {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        logger.info(f"Configuration chargée avec succès ({len(cfg)} clés)")
        return cfg
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la config: {e}")
        return {}

import signal

def main(config_path: str = None):
    logger.info("=== DÉMARRAGE MINIMA v2.4 (Mode intelligent) ===")
    try:
        ensure_paths()
        cfg = load_config(config_path)

        mode = cfg.get("mode", "scrap")
        max_depth = int(cfg.get("max_depth", 1))
        delay = cfg.get("delay", 0)
        accepted_languages = cfg.get("accepted_languages", ["en"])
        logger.info(f"Pipeline mode: {mode}, max_depth: {max_depth}, accepted_languages: {accepted_languages}")

        export_flush_every = int(cfg.get("export_flush_every", 10))

        logger.info(f"Pipeline mode: {mode}, max_depth: {max_depth}, "
                    f"accepted_languages: {accepted_languages}, export_flush_every: {export_flush_every}")

        valid_plugins = validate_all(PLUGIN_DIR)
        logger.info(f"{len(valid_plugins)} plugin(s) validé(s) et prêt(s) à l'emploi")

        urls = cfg.get("urls", [])
        os.makedirs(os.path.dirname(QUEUE_PATH), exist_ok=True)
        queue = PersistentQueue(QUEUE_PATH)
        analyzer = GenericAnalyzer(logger=logger)
        exporter = Exporter(flush_every=export_flush_every)
        scraper = Scraper()

        for url in urls:
            queue.add({"url": url, "depth": 0, "score": 0})

        results = []

        # Gestion Ctrl+C
        def handle_sigint(sig, frame):
            logger.warning("Interrupt reçu, flush final en cours...")
            exporter.flush()
            logger.info("Flush final terminé, arrêt du pipeline.")
            exit(0)

        signal.signal(signal.SIGINT, handle_sigint)

        while not queue.is_empty():
            urls_to_fetch = queue.remaining_urls()
            if not urls_to_fetch:
                logger.info("Plus d'URLs à traiter")
                break

            html_map = scraper.fetch_all([item["url"] for item in urls_to_fetch])

            for item in urls_to_fetch:
                url = item["url"]
                depth = item["depth"]
                html = html_map.get(url)

                if not html:
                    logger.warning(f"Contenu vide ou échec pour {url}")
                    queue.mark_processed(item)
                    continue

                lang = analyzer.detect_language(html)
                if lang not in accepted_languages:
                    logger.info(f"Ignoré {url} car langue {lang} non acceptée")
                    queue.mark_processed(item)
                    continue

                result = analyzer.analyze(html, url)
                result['score'] = item.get('score', 0)  # <-- Ajoute le score ici


                for plugin_module in valid_plugins:
                    try:
                        if hasattr(plugin_module, "process"):
                            plugin_result = plugin_module.process(url, html)
                            if plugin_result:
                                result.update(plugin_result)
                    except Exception as e:
                        logger.warning(f"Erreur plugin {getattr(plugin_module, '__name__', 'unknown')}: {e}")

                queue.mark_processed(item)
                logger.info(f"Analyse terminée pour {url}")

                # Ajout au buffer et flush si nécessaire
                exporter.add_results([result])

                if "crawl" in mode and depth < max_depth:
                    links = result.get("links", [])
                    for link in links:
                        full_url = urljoin(url, link)
                        preview_html = scraper.fetch_preview(full_url)
                        lang = analyzer.detect_language(preview_html)
                        if lang in accepted_languages:
                            queue.add({"url": full_url, "depth": depth + 1, "score": 0})
                        else:
                            logger.info(f"Ignoré {full_url} car langue {lang} non acceptée")

                if delay > 0:
                    time.sleep(delay)

        # Flush final pour tout ce qui reste dans le buffer
        exporter.flush()
        logger.info("=== FIN DU PIPELINE MINIMA ===")

    except MinimaError as e:
        logger.error(f"Erreur Minima détectée: {e}")
    except Exception as e:
        logger.exception(f"Erreur critique non gérée: {e}")

if __name__ == "__main__":
    main()