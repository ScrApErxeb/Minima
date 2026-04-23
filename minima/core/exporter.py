from __future__ import annotations
import json
import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Any
from minima.core.logger import logger

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DB_DIR = Path("Crawl_data")
EXPORT_DB_DIR.mkdir(parents=True, exist_ok=True)

def _timestamp() -> str:
    """Retourne un timestamp compact pour nommer les fichiers d’export."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class Exporter:
    """Gère l'écriture des résultats au format JSON, CSV et SQLite."""

    def __init__(self, output_dir: Path = EXPORT_DIR, output_db_dir: Path = EXPORT_DB_DIR,
                 flush_every: int = 10) -> None:
        self.output_dir = output_dir
        self.output_db_dir = output_db_dir
        # La valeur vient maintenant de la config via le main
        self.flush_every = max(1, flush_every) 
        self._buffer = []

    def _flush_buffer(self):
        """Vide le buffer vers les fichiers et la base de données."""
        if self._buffer:
            ts = _timestamp()
            jour = datetime.now().strftime("%Y%m%d")
            
            self.save_json(self._buffer, f"results_flush_{ts}.json")
            self.save_csv(self._buffer, f"results_flush_{ts}.csv")
            # Le nom du fichier DB reste fixe par jour pour centraliser les données
            self.save_sqlite(self._buffer, f"crawl_{jour}.db", table_name="results")
            
            logger.info(f"💾 Flush effectué : {len(self._buffer)} items enregistrés.")
            self._buffer.clear()

    def add_results(self, results: Iterable[Mapping[str, Any]]):
        """Ajoute des résultats au buffer et déclenche le flush si le seuil est atteint."""
        self._buffer.extend(results)
        if len(self._buffer) >= self.flush_every:
            self._flush_buffer()

    def flush(self):
        """Force l'exportation de tout ce qui reste dans le buffer (fin de programme)."""
        if not self._buffer:
            return
        logger.info(f"Dernier flush de {len(self._buffer)} résultats avant fermeture.")
        self._flush_buffer()

    def save_json(self, data: Iterable[Mapping[str, Any]], filename: str | None = None) -> Path:
        filename = filename or f"results_{_timestamp()}.json"
        path = self.output_dir / filename
        try:
            with open(path, "w", encoding="utf-8") as jf:
                json.dump(list(data), jf, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Export JSON failed: {e}")
        return path

    def save_csv(self, data: Iterable[Mapping[str, Any]], filename: str | None = None) -> Path:
        filename = filename or f"results_{_timestamp()}.csv"
        path = self.output_dir / filename
        data_list = list(data)
        try:
            if not data_list: return path
            with open(path, "w", newline="", encoding="utf-8") as cf:
                writer = csv.DictWriter(cf, fieldnames=data_list[0].keys())
                writer.writeheader()
                writer.writerows(data_list)
        except Exception as e:
            logger.error(f"Export CSV failed: {e}")
        return path

    def save_sqlite(self, data: list[dict], filename: str | None = None, table_name: str = "results") -> Path:
        if filename is None:
            filename = f"crawl_{datetime.now().strftime('%Y%m%d')}.db"

        path = self.output_db_dir / filename
        if not data: return path

        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # 1. S'assurer que la table principale existe au moins avec l'URL
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (url TEXT PRIMARY KEY)")
        
        # 2. TABLE À PART pour les mots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_frequencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                word TEXT,
                count INTEGER,
                FOREIGN KEY(url) REFERENCES results(url)
            )
        """)

        # --- SÉCURITÉ : AJOUT DYNAMIQUE DES COLONNES ---
        # On regarde ce qu'il y a déjà dans la table 'results'
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_cols = [col[1] for col in cursor.fetchall()]

        for row in data:
            for col_name in row.keys():
                # On ignore 'top_words' car il va dans sa propre table
                if col_name not in existing_cols and col_name != "top_words":
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} TEXT")
                    existing_cols.append(col_name) # Évite de tenter l'ajout plusieurs fois

        # --- INSERTION ---
        for row in data:
            url = row.get("url")
            
            # Insertion table principale
            main_data = {k: v for k, v in row.items() if k != "top_words"}
            cols = ", ".join(main_data.keys())
            placeholders = ", ".join("?" for _ in main_data)
            
            # Conversion des listes (comme 'links') en texte pour SQLite
            values = []
            for v in main_data.values():
                if isinstance(v, (list, dict)):
                    values.append(json.dumps(v, ensure_ascii=False))
                else:
                    values.append(str(v))
            
            cursor.execute(f"INSERT OR REPLACE INTO {table_name} ({cols}) VALUES ({placeholders})", tuple(values))

            # Insertion table des mots
            top_words = row.get("top_words")
            if top_words and isinstance(top_words, dict):
                cursor.execute("DELETE FROM word_frequencies WHERE url = ?", (url,))
                for word, count in top_words.items():
                    cursor.execute("INSERT INTO word_frequencies (url, word, count) VALUES (?, ?, ?)", (url, word, count))

        conn.commit()
        conn.close()
        return path
        if filename is None:
            filename = f"crawl_{datetime.now().strftime('%Y%m%d')}.db"

        path = self.output_db_dir / filename
        if not data: return path

        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # 1. Création des deux tables
        # Table principale (sans la colonne top_words qui devient inutile ici)
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (url TEXT PRIMARY KEY, title TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
        
        # TABLE À PART pour les mots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_frequencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                word TEXT,
                count INTEGER,
                FOREIGN KEY(url) REFERENCES results(url)
            )
        """)

        for row in data:
            url = row.get("url")
            
            # 2. Insertion dans la table principale (on filtre top_words pour cette table)
            main_data = {k: v for k, v in row.items() if k != "top_words"}
            cols = ", ".join(main_data.keys())
            placeholders = ", ".join("?" for _ in main_data)
            cursor.execute(f"INSERT OR REPLACE INTO {table_name} ({cols}) VALUES ({placeholders})", tuple(str(v) for v in main_data.values()))

            # 3. Insertion dans la table des mots (si le plugin a renvoyé des données)
            top_words = row.get("top_words")
            if top_words and isinstance(top_words, dict):
                # On nettoie les anciens mots pour cette URL avant de remettre les nouveaux
                cursor.execute("DELETE FROM word_frequencies WHERE url = ?", (url,))
                
                for word, count in top_words.items():
                    cursor.execute(
                        "INSERT INTO word_frequencies (url, word, count) VALUES (?, ?, ?)",
                        (url, word, count)
                    )

        conn.commit()
        conn.close()
        return path
        """Exporte en SQLite avec détection automatique des colonnes des plugins."""
        if filename is None:
            filename = f"crawl_{datetime.now().strftime('%Y%m%d')}.db"

        path = self.output_db_dir / filename
        if not data: return path

        # Extraction de toutes les clés présentes (pour gérer les nouveaux plugins)
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())
        all_columns = sorted(list(all_columns))

        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # 1. Création de table ultra-basique si inexistante
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (url TEXT PRIMARY KEY)")

        # 2. Mise à jour dynamique des colonnes (pour top_words, nlp_result, etc.)
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_cols = [col[1] for col in cursor.fetchall()]

        for col in all_columns:
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} TEXT")

        # 3. Insertion des données
        for row in data:
            cols = ", ".join(row.keys())
            placeholders = ", ".join("?" for _ in row)
            # On convertit les dicts (comme top_words) en chaînes JSON pour SQLite
            values = []
            for val in row.values():
                if isinstance(val, (dict, list)):
                    values.append(json.dumps(val, ensure_ascii=False))
                else:
                    values.append(str(val))
            
            cursor.execute(f"INSERT OR REPLACE INTO {table_name} ({cols}) VALUES ({placeholders})", tuple(values))

        conn.commit()
        conn.close()
        return path