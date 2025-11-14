import os
import time
import yaml
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


def main(config_path: str = None):
    logger.info("=== DÉMARRAGE MINIMA v2.0 (Mode intelligent) ===")

    try:
        ensure_paths()
        cfg = load_config(config_path)

        mode = cfg.get("mode", "scrap")
        max_depth = int(cfg.get("max_depth", 1))
        delay = cfg.get("delay", 0)

        logger.info(f"Pipeline mode: {mode}, max_depth: {max_depth}")

        # Validation et chargement sécurisé des plugins
        logger.info(f"Validation des plugins dans {PLUGIN_DIR}")
        valid_plugins = validate_all(PLUGIN_DIR)
        logger.info(f"{len(valid_plugins)} plugin(s) validé(s) et prêt(s) à l'emploi")

        urls = cfg.get("urls", [])

        # Initialisation queue
        os.makedirs(os.path.dirname(QUEUE_PATH), exist_ok=True)
        queue = PersistentQueue(QUEUE_PATH)
        analyzer = GenericAnalyzer(logger=logger)
        exporter = Exporter()
        scraper = Scraper()

        if queue.is_empty() and urls:
            logger.info(f"Queue vide au démarrage, ajout de {len(urls)} URLs depuis config.yaml")
            for u in urls:
                queue.add(u)

        results = []
        depth = 0

        while not queue.is_empty() and depth < max_depth:
            urls_to_fetch = queue.remaining_urls()
            if not urls_to_fetch:
                logger.info("Plus d'URLs à traiter à cette profondeur")
                break

            html_map = scraper.fetch_all(urls_to_fetch)

            new_urls = []
            for url, html in html_map.items():
                if not html:
                    logger.warning(f"Contenu vide ou échec pour {url}")
                    queue.mark_processed(url)
                    continue

                # Analyse du contenu
                result = analyzer.analyze(html, url)

                # Application des plugins validés
                for plugin_module in valid_plugins:
                    plugin_name = getattr(plugin_module, "__name__", "unknown")
                    try:
                        if hasattr(plugin_module, "process"):
                            plugin_result = plugin_module.process(url, html)
                            if plugin_result:
                                result.update(plugin_result)
                        else:
                            logger.warning(f"Plugin {plugin_name} n’a pas de méthode process()")
                    except Exception as e:
                        logger.warning(f"Erreur plugin {plugin_name}: {e}")

                results.append(result)
                queue.mark_processed(url)
                logger.info(f"Analyse terminée pour {url}")

                if "crawl" in mode:
                    # Ajouter les liens trouvés à la queue pour le crawl
                    links = result.get("links", [])
                    for link in links:
                        queue.add(link)

                if delay > 0:
                    logger.info(f"Pause de {delay}s avant la prochaine URL")
                    time.sleep(delay)

            depth += 1
            logger.info(f"=== Fin de profondeur {depth} ===")

        if results:
            logger.info(f"Exportation de {len(results)} résultats")
            exporter.export_results(results)
        else:
            logger.warning("Aucun résultat à exporter")

        logger.info("=== FIN DU PIPELINE MINIMA ===")

    except MinimaError as e:
        logger.error(f"Erreur Minima détectée: {e}")
    except Exception as e:
        logger.exception(f"Erreur critique non gérée: {e}")


if __name__ == "__main__":
    main()
