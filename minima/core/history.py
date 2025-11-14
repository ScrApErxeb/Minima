# minima/core/history.py

class HistoryManager:
    """Stocke les résultats et métadonnées des pages traitées."""

    def __init__(self):
        self.records = []

    def save_page_features(self, result: dict):
        """Ajoute le résultat d'une page à l'historique."""
        self.records.append(result)

    def get_all(self):
        """Retourne toutes les pages stockées."""
        return self.records

    def clear(self):
        """Réinitialise l'historique."""
        self.records = []
