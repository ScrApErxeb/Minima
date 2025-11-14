import os
import yaml
from unittest.mock import MagicMock

from minima.main import load_config
from minima.core.generic_analyzer import GenericAnalyzer
from minima.core.queue import PersistentQueue

# --- Création d'une config de test YAML ---
test_config_path = "config_test.yaml"
test_config = {
    "urls": [
        "https://fr.wikipedia.org/wiki/Burkina_Faso",
        "https://en.wikipedia.org/wiki/Mali",
        "https://es.wikipedia.org/wiki/España"
    ],
    "accept_languages": ["en", "fr"]
}

with open(test_config_path, "w", encoding="utf-8") as f:
    yaml.dump(test_config, f, default_flow_style=False)

# --- Initialisation des composants ---
cfg = load_config(test_config_path)
accepted_languages = cfg.get("accept_languages", ["en"])

queue = PersistentQueue("queue_test.json")
analyzer = GenericAnalyzer(logger=None)  # ou un logger mocké
queue.clear()  # Nettoie pour le test

# --- Ajout des URLs à la queue ---
for url in cfg["urls"]:
    queue.add({"url": url, "depth": 0, "score": 0})

# --- Mock du fetch HTML pour ne pas dépendre d'internet ---
fake_html_map = {
    "https://fr.wikipedia.org/wiki/Burkina_Faso": "<html lang='fr'>Bonjour</html>",
    "https://en.wikipedia.org/wiki/Mali": "<html lang='en'>Hello</html>",
    "https://es.wikipedia.org/wiki/España": "<html lang='es'>Hola</html>"
}

# --- Test de traitement des URLs ---
while not queue.is_empty():
    item = queue.get()
    url = item["url"]
    html = fake_html_map.get(url, "")

    # Détection de la langue
    lang = analyzer.detect_language(html)
    lang_normalized = lang.strip().lower()
    accepted_normalized = [l.strip().lower() for l in accepted_languages]

    if lang_normalized not in accepted_normalized:
        print(f"Ignoré {url} car langue {lang_normalized} non acceptée")
    else:
        print(f"Traité {url} car langue {lang_normalized} acceptée")

    queue.mark_processed(item)

# --- Nettoyage ---
os.remove(test_config_path)
os.remove("queue_test.json")
