# Minima v0.9

Minima est un framework modulaire de Crawling extensible par plugins.

## Fonctionnalités principales
- Système de configuration dynamique (`config/config.yaml`)
- Scraping multi-threads configurable
- Analyse générique et par plugin
- Système de queue persistant
- Export JSON/CSV incrémental ou en fin d’exécution
- Logs rotatifs configurables
- Pipeline de traitement multi-plugins
- Métriques globales (succès, échecs, latence, taille, RPS)

## Initialisation & Installation

Suivez ces étapes selon votre système (Windows / Linux / macOS). Remplacez l'URL du dépôt si nécessaire.

1. Cloner le dépôt et se placer dans le projet
2. Créer et activer un environnement virtuel (Python)
3. Installer les dépendances
4. Copier le fichier de configuration exemple
5. Lancer l'application (ajuster l'entrée si nécessaire)

Windows (PowerShell)
```powershell
git clone https://github.com/mon-orga/Minima.git
cd Minima
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item config\config.example.yaml config\config.yaml
python -m minima  # ou python main.py selon le projet
```

Windows (CMD)
```cmd
git clone https://github.com/mon-orga/Minima.git
cd Minima
py -3 -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy config\config.example.yaml config\config.yaml
python -m minima
```

Linux / macOS (bash/zsh)
```bash
git clone https://github.com/mon-orga/Minima.git
cd Minima
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml
python -m minima  # ou python main.py selon le projet
```

Remarques:
- Si le projet n'est pas en Python, adaptez la création d'environnement et l'installation (ex. npm, go, cargo).
- Ajustez le chemin et le nom du point d'entrée si nécessaire.
- Pour exécuter plusieurs commandes en une sélection, sélectionner simplement le bloc correspondant à votre OS.
