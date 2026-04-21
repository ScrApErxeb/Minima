# 🕵️ Minima v0.9
**Framework de Crawling modulaire et extensible.**

Minima est un framework robuste conçu pour le scraping intensif, reposant sur une architecture orientée plugins qui sépare la collecte, l'analyse et l'exportation des données.

---

## 🚀 Fonctionnalités Clés

* **Architecture Modulaire :** Pipeline de traitement extensible via le système de plugins (`minima/plugins/`).
* **Performance :** Scraping multi-threadé avec gestion de file d'attente (**Queue**) persistante.
* **Configuration Dynamique :** Gestion avancée via YAML (`config/config.yaml`).
* **Observabilité :** Métriques en temps réel (RPS, latence, succès/échecs) et logs rotatifs automatisés.
* **Export Flexible :** Support incrémental pour les formats JSON et CSV.
* **Sécurité :** Système de validation de plugins et hachage de sécurité.

---

## 🛠️ Installation & Configuration

### 1. Cloner le projet
```bash
git clone [https://github.com/ScrApErxeb/Minima.git](https://github.com/ScrApErxeb/Minima.git)
cd Minima

2. Préparer l'environnement

Choisissez la méthode adaptée à votre système :
🪟 Windows (PowerShell)
PowerShell

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item config\default.yaml config\config.yaml

🐧 Linux / 🍎 macOS
Bash

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/default.yaml config/config.yaml

🚦 Commande de Lancement

Pour garantir la résolution correcte des modules internes (core, utils, plugins), utilisez la commande suivante à la racine du projet :
Mode Standard (Recommandé)

Exécute le projet en tant que module Python :
Bash

python -m minima.main

Mode Interface (CLI)

Si vous utilisez le point d'entrée CLI racine :
Bash

python cli.py

Mode Docker
Bash

docker build -t minima .
docker run --rm minima

📂 Structure du Projet

    minima/core/ : Le cœur du moteur (Scraper, Manager, Intelligence).

    minima/plugins/ : Vos analyseurs et extensions personnalisés.

    config/ : Fichiers de configuration YAML.

    logs/ : Sorties de logs et historiques d'exécution.

    tests/ : Suite complète de tests unitaires (via pytest).

🧪 Tests

Pour lancer la suite de tests et vérifier l'intégrité du système :
Bash

pytest

© 2026 Minima Framework - Modulaire, Rapide, Efficace.