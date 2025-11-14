# minima/core/intelligence.py

class IntelligenceManager:
    """Gestion basique de l'intelligence du pipeline Minima."""

    def score_page(self, result: dict) -> float:
        """
        Calcule un score simple pour une page.
        Exemple : liens + images + mots.
        """
        links = result.get("link_count", 0)
        images = result.get("image_count", 0)
        words = result.get("word_count", 0)

        # Score pondéré simple
        score = links * 0.3 + images * 0.2 + words * 0.5
        return score

    def is_relevant(self, url: str) -> bool:
        """
        Placeholder : décide si une URL est pertinente pour le crawl.
        Phase I : accepte tout.
        """
        return True

    def prioritize_queue(self, queue):
        """
        Placeholder : réorganiser la queue selon les scores.
        Implémentation avancée en Phase II.
        """
        pass
