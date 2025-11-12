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
- python -m venv minima_env

```
Windows
```
- minima_env\Scripts\Activate.ps1 
```
Linux & Mac
```
source scripts/bin/activate
```

```
- pip install -r requirements.txt
```
```
- python -m minima.main
```
