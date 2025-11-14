import os
import json
from minima.core.logger import logger

class PersistentQueue:
    def __init__(self, path, flush_every=1):
        self.path = path
        self.flush_every = max(1, flush_every)  # Nombre d'opérations avant flush
        self._counter = 0
        # Chaque item est un dict {"url": ..., "depth": ..., "score": ...}
        self.data = {"pending": [], "processed": [], "scores": {}}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data["pending"] = loaded.get("pending", [])
                    self.data["processed"] = loaded.get("processed", [])
                    self.data["scores"] = loaded.get("scores", {})
                # Nettoyage pour éviter les doublons
                self.data["pending"] = [item for item in self.data["pending"] if item not in self.data["processed"]]
                self._save()
                logger.info(f"Queue chargée depuis {self.path} "
                            f"({len(self.data['pending'])} en attente, "
                            f"{len(self.data['processed'])} traitées)")
            except Exception as e:
                logger.warning(f"Échec du chargement de la queue: {e}")
        else:
            logger.info(f"Aucune queue trouvée, création d'une nouvelle: {self.path}")
            self._save()

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la queue: {e}")

    def _maybe_flush(self):
        self._counter += 1
        if self._counter >= self.flush_every:
            self._save()
            self._counter = 0

    def add(self, item, score=0):
        """Ajoute un item dict à la queue si il n’existe pas déjà."""
        if item not in self.data["pending"] and item not in self.data["processed"]:
            self.data["pending"].append(item)
            self.data["scores"][item["url"]] = score
            logger.info(f"Added to queue: {item}")
            self._maybe_flush()

    def get(self):
        """Récupère l’item avec le score le plus élevé."""
        if self.is_empty():
            return None
        self.data["pending"].sort(key=lambda x: self.data["scores"].get(x["url"], 0), reverse=True)
        item = self.data["pending"].pop(0)
        self._maybe_flush()
        return item

    def mark_processed(self, item):
        """Marque un item dict comme traité et nettoie pending."""
        self.data["pending"] = [i for i in self.data["pending"] if i != item]
        if item not in self.data["processed"]:
            self.data["processed"].append(item)
            self.data["scores"].pop(item["url"], None)
            logger.info(f"Marqué comme traité: {item}")
        self._maybe_flush()

    def force_flush(self):
        """Flush immédiat, par ex. avant Ctrl+C."""
        self._save()
        logger.info("Queue flush forcé")

    def is_empty(self):
        return len(self.data["pending"]) == 0

    def clear(self):
        self.data = {"pending": [], "processed": [], "scores": {}}
        self._save()
        logger.info("Queue réinitialisée")

    def remaining_urls(self) -> list[dict]:
        return sorted(
            self.data.get("pending", []),
            key=lambda x: self.data["scores"].get(x["url"], 0),
            reverse=True
        )
