import os
import json
from minima.core.logger import logger

class PersistentQueue:
    def __init__(self, path):
        self.path = path
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

    def add(self, item, score=0):
        """Ajoute un item dict à la queue si il n’existe pas déjà."""
        if item not in self.data["pending"] and item not in self.data["processed"]:
            self.data["pending"].append(item)
            self.data["scores"][item["url"]] = score
            logger.info(f"Added to queue: {item}")
            self._save()

    def get(self):
        """Récupère l’item avec le score le plus élevé."""
        if self.is_empty():
            return None
        # Trier par score
        self.data["pending"].sort(key=lambda x: self.data["scores"].get(x["url"], 0), reverse=True)
        item = self.data["pending"].pop(0)
        self._save()
        return item

    def mark_processed(self, item):
        """Marque un item dict comme traité et nettoie pending."""
        # Supprime toutes les occurences de cet item dans pending
        self.data["pending"] = [i for i in self.data["pending"] if i != item]
        if item not in self.data["processed"]:
            self.data["processed"].append(item)
            # Supprime le score
            self.data["scores"].pop(item["url"], None)
            logger.info(f"Marqué comme traité: {item}")
        self._save()

    def is_empty(self):
        return len(self.data["pending"]) == 0

    def clear(self):
        self.data = {"pending": [], "processed": [], "scores": {}}
        self._save()
        logger.info("Queue réinitialisée")

    def remaining_urls(self) -> list[dict]:
        """Retourne les items dict encore à traiter, triés par score."""
        return sorted(
            self.data.get("pending", []),
            key=lambda x: self.data["scores"].get(x["url"], 0),
            reverse=True
        )
